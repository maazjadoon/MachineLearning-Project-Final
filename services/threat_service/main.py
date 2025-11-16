"""
Cyber Sentinel ML - Threat Detection Service
Enterprise-grade FastAPI microservice for real-time threat detection
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from prometheus_fastapi_instrumentator import Instrumentator
import time
import logging
import asyncio
import aioredis
import asyncpg
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional
import uvicorn
import os
from datetime import datetime
import json
import traceback

# Import ML components
from attack_categories import auto_detector
from cyber_sentinel_mod import CyberSentinelMod
from port_scan_detector import PortScanDetector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter('threat_service_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('threat_service_request_duration_seconds', 'Request duration')
ACTIVE_CONNECTIONS = Gauge('threat_service_active_connections', 'Active connections')
THREAT_DETECTIONS = Counter('threat_detections_total', 'Total threat detections', ['attack_type', 'severity'])
ML_INFERENCE_TIME = Histogram('ml_inference_duration_seconds', 'ML inference duration')
SYSTEM_HEALTH = Gauge('threat_service_health', 'Service health status')

# Global variables
redis_client = None
db_pool = None
ml_model = None
port_scanner = None

# Security
security = HTTPBearer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("🚀 Starting Threat Detection Service...")
    
    # Initialize Redis
    global redis_client
    try:
        redis_client = await aioredis.from_url(
            os.getenv('REDIS_URL', 'redis://localhost:6379'),
            encoding='utf-8',
            decode_responses=True
        )
        await redis_client.ping()
        logger.info("✅ Redis connected")
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")
    
    # Initialize Database
    global db_pool
    try:
        db_pool = await asyncpg.create_pool(
            os.getenv('DATABASE_URL', 'postgresql://user:pass@localhost/cyber_sentinel'),
            min_size=5,
            max_size=20
        )
        logger.info("✅ Database connected")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
    
    # Initialize ML Models
    global ml_model, port_scanner
    try:
        ml_model = CyberSentinelMod()
        port_scanner = PortScanDetector()
        logger.info("✅ ML models loaded")
    except Exception as e:
        logger.error(f"❌ ML model loading failed: {e}")
    
    SYSTEM_HEALTH.set(1)
    logger.info("🎉 Threat Detection Service ready!")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Threat Detection Service...")
    SYSTEM_HEALTH.set(0)
    
    if redis_client:
        await redis_client.close()
    if db_pool:
        await db_pool.close()
    
    logger.info("✅ Service shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="Cyber Sentinel - Threat Detection Service",
    description="Enterprise-grade real-time threat detection microservice",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Prometheus instrumentation
Instrumentator().instrument(app).expose(app)

# Rate limiting
class RateLimiter:
    def __init__(self):
        self.requests = {}
    
    async def is_allowed(self, key: str, limit: int = 1000, window: int = 60) -> bool:
        now = time.time()
        if key not in self.requests:
            self.requests[key] = []
        
        # Remove old requests
        self.requests[key] = [req_time for req_time in self.requests[key] if now - req_time < window]
        
        if len(self.requests[key]) >= limit:
            return False
        
        self.requests[key].append(now)
        return True

rate_limiter = RateLimiter()

# Dependencies
async def get_redis():
    return redis_client

async def get_db():
    return db_pool

async def verify_credentials(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT credentials"""
    try:
        # Implement JWT verification logic here
        return credentials.credentials
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid credentials")

# Health endpoints
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0",
        "services": {}
    }
    
    # Check Redis
    if redis_client:
        try:
            await redis_client.ping()
            health_status["services"]["redis"] = "healthy"
        except:
            health_status["services"]["redis"] = "unhealthy"
            health_status["status"] = "degraded"
    else:
        health_status["services"]["redis"] = "not_connected"
        health_status["status"] = "degraded"
    
    # Check Database
    if db_pool:
        try:
            async with db_pool.acquire() as conn:
                await conn.execute("SELECT 1")
            health_status["services"]["database"] = "healthy"
        except:
            health_status["services"]["database"] = "unhealthy"
            health_status["status"] = "degraded"
    else:
        health_status["services"]["database"] = "not_connected"
        health_status["status"] = "degraded"
    
    # Check ML Models
    if ml_model and port_scanner:
        health_status["services"]["ml_models"] = "healthy"
    else:
        health_status["services"]["ml_models"] = "not_loaded"
        health_status["status"] = "degraded"
    
    status_code = 200 if health_status["status"] == "healthy" else 503
    return JSONResponse(content=health_status, status_code=status_code)

@app.get("/ready", tags=["Health"])
async def readiness_check():
    """Readiness check for Kubernetes"""
    return {"status": "ready"}

@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    """Prometheus metrics endpoint"""
    return generate_latest()

# API endpoints
@app.post("/api/v1/threat/detect", tags=["Threat Detection"])
async def detect_threat(
    request: Request,
    background_tasks: BackgroundTasks,
    redis=Depends(get_redis),
    db=Depends(get_db),
    credentials: str = Depends(verify_credentials)
):
    """
    Detect threats from network packet data
    """
    start_time = time.time()
    
    try:
        # Rate limiting
        client_ip = request.client.host
        if not await rate_limiter.is_allowed(client_ip):
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        # Parse request data
        data = await request.json()
        packet_data = data.get('packet', {})
        
        if not packet_data:
            raise HTTPException(status_code=400, detail="No packet data provided")
        
        # Add timestamp
        packet_data['timestamp'] = datetime.utcnow().isoformat()
        
        # Run automatic detection
        auto_detections = auto_detector.analyze_packet(packet_data)
        
        # Run ML detection
        ml_result = {}
        if ml_model:
            inference_start = time.time()
            try:
                ml_result = ml_model.classify(packet_data)
                ML_INFERENCE_TIME.observe(time.time() - inference_start)
            except Exception as e:
                logger.error(f"ML inference failed: {e}")
                ml_result = {"error": str(e)}
        
        # Combine results
        detection_result = {
            "timestamp": packet_data['timestamp'],
            "packet_id": data.get('packet_id', f"pkt_{int(time.time()*1000)}"),
            "source_ip": packet_data.get('srcip', 'unknown'),
            "destination_ip": packet_data.get('dstip', 'unknown'),
            "protocol": packet_data.get('protocol', 'unknown'),
            "threat_detected": False,
            "detections": []
        }
        
        # Process automatic detections
        if auto_detections:
            best_detection = max(auto_detections, key=lambda x: x['confidence'])
            detection_result.update({
                "threat_detected": True,
                "attack_type": best_detection['attack_name'],
                "attack_category": best_detection['category'],
                "confidence": best_detection['confidence'],
                "severity": best_detection['severity'],
                "detection_method": "automatic_rules",
                "auto_response": best_detection['auto_response'],
                "matched_rules": best_detection['matched_rules'],
                "description": best_detection['description']
            })
            detection_result["detections"].append({
                "method": "automatic_rules",
                "result": best_detection
            })
            
            # Update metrics
            THREAT_DETECTIONS.labels(
                attack_type=best_detection['attack_name'],
                severity=best_detection['severity']
            ).inc()
        
        # Process ML detection
        if ml_result and 'error' not in ml_result:
            detection_result["detections"].append({
                "method": "ml_models",
                "result": ml_result
            })
            
            # If automatic detection didn't find threat, use ML result
            if not detection_result["threat_detected"] and ml_result.get('threat_detected'):
                detection_result.update({
                    "threat_detected": True,
                    "attack_type": ml_result.get('attack_type', 'Unknown'),
                    "confidence": ml_result.get('confidence', 0),
                    "severity": ml_result.get('severity', 'UNKNOWN'),
                    "detection_method": "ml_models"
                })
                
                THREAT_DETECTIONS.labels(
                    attack_type=ml_result.get('attack_type', 'Unknown'),
                    severity=ml_result.get('severity', 'UNKNOWN')
                ).inc()
        
        # Store in database (async)
        background_tasks.add_task(store_detection, detection_result, db)
        
        # Cache in Redis
        if redis:
            background_tasks.add_task(cache_detection, detection_result, redis)
        
        # Log detection
        if detection_result["threat_detected"]:
            logger.warning(
                f"🚨 THREAT DETECTED: {detection_result.get('attack_type', 'Unknown')} "
                f"from {detection_result['source_ip']} to {detection_result['destination_ip']} "
                f"| Confidence: {detection_result.get('confidence', 0):.2%} | "
                f"Severity: {detection_result.get('severity', 'UNKNOWN')}"
            )
        
        # Update metrics
        REQUEST_DURATION.observe(time.time() - start_time)
        REQUEST_COUNT.labels(
            method="POST",
            endpoint="/api/v1/threat/detect",
            status="200"
        ).inc()
        
        return detection_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Detection error: {e}")
        REQUEST_COUNT.labels(
            method="POST",
            endpoint="/api/v1/threat/detect",
            status="500"
        ).inc()
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")

@app.post("/api/v1/threat/batch-detect", tags=["Threat Detection"])
async def batch_detect_threats(
    request: Request,
    background_tasks: BackgroundTasks,
    redis=Depends(get_redis),
    db=Depends(get_db),
    credentials: str = Depends(verify_credentials)
):
    """
    Batch threat detection for multiple packets
    """
    try:
        data = await request.json()
        packets = data.get('packets', [])
        
        if not packets:
            raise HTTPException(status_code=400, detail="No packets provided")
        
        if len(packets) > 100:
            raise HTTPException(status_code=400, detail="Too many packets (max 100)")
        
        results = []
        for packet in packets:
            try:
                # Create individual detection request
                detection_data = {"packet": packet}
                
                # Process detection
                result = await detect_threat(
                    request=request,
                    background_tasks=background_tasks,
                    redis=redis,
                    db=db,
                    credentials=credentials
                )
                results.append(result)
                
            except Exception as e:
                results.append({
                    "packet_id": packet.get('packet_id', 'unknown'),
                    "error": str(e),
                    "threat_detected": False
                })
        
        return {
            "batch_id": f"batch_{int(time.time()*1000)}",
            "processed_packets": len(results),
            "threats_found": sum(1 for r in results if r.get('threat_detected', False)),
            "results": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch detection error: {e}")
        raise HTTPException(status_code=500, detail=f"Batch detection failed: {str(e)}")

@app.get("/api/v1/threat/stats", tags=["Analytics"])
async def get_threat_stats(
    redis=Depends(get_redis),
    db=Depends(get_db),
    credentials: str = Depends(verify_credentials)
):
    """Get threat detection statistics"""
    try:
        stats = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_detections": 0,
            "threats_detected": 0,
            "attack_types": {},
            "severity_distribution": {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        }
        
        # Get stats from Redis
        if redis:
            try:
                total_detections = await redis.get("stats:total_detections") or 0
                threats_detected = await redis.get("stats:threats_detected") or 0
                
                stats["total_detections"] = int(total_detections)
                stats["threats_detected"] = int(threats_detected)
                
                # Get attack type stats
                attack_types = await redis.hgetall("stats:attack_types")
                stats["attack_types"] = {k: int(v) for k, v in attack_types.items()}
                
                # Get severity distribution
                severity_dist = await redis.hgetall("stats:severity_distribution")
                stats["severity_distribution"].update({k: int(v) for k, v in severity_dist.items()})
                
            except Exception as e:
                logger.error(f"Redis stats error: {e}")
        
        return stats
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail=f"Stats retrieval failed: {str(e)}")

@app.get("/api/v1/threat/history", tags=["Analytics"])
async def get_threat_history(
    limit: int = 100,
    offset: int = 0,
    db=Depends(get_db),
    credentials: str = Depends(verify_credentials)
):
    """Get threat detection history"""
    try:
        if not db:
            raise HTTPException(status_code=503, detail="Database not available")
        
        async with db.acquire() as conn:
            # Get total count
            count_query = "SELECT COUNT(*) FROM threat_detections"
            total_count = await conn.fetchval(count_query)
            
            # Get paginated results
            query = """
                SELECT * FROM threat_detections 
                ORDER BY timestamp DESC 
                LIMIT $1 OFFSET $2
            """
            rows = await conn.fetch(query, limit, offset)
            
            detections = [dict(row) for row in rows]
            
            return {
                "total_count": total_count,
                "limit": limit,
                "offset": offset,
                "detections": detections
            }
        
    except Exception as e:
        logger.error(f"History error: {e}")
        raise HTTPException(status_code=500, detail=f"History retrieval failed: {str(e)}")

# Background tasks
async def store_detection(detection: Dict[str, Any], db_pool):
    """Store detection in database"""
    if not db_pool:
        return
    
    try:
        async with db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO threat_detections 
                (timestamp, packet_id, source_ip, destination_ip, protocol, 
                 threat_detected, attack_type, attack_category, confidence, 
                 severity, detection_method, auto_response, matched_rules, description)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                """,
                detection.get('timestamp'),
                detection.get('packet_id'),
                detection.get('source_ip'),
                detection.get('destination_ip'),
                detection.get('protocol'),
                detection.get('threat_detected', False),
                detection.get('attack_type'),
                detection.get('attack_category'),
                detection.get('confidence'),
                detection.get('severity'),
                detection.get('detection_method'),
                detection.get('auto_response'),
                json.dumps(detection.get('matched_rules', [])),
                detection.get('description')
            )
    except Exception as e:
        logger.error(f"Database storage error: {e}")

async def cache_detection(detection: Dict[str, Any], redis_client):
    """Cache detection in Redis"""
    if not redis_client:
        return
    
    try:
        # Update counters
        await redis_client.incr("stats:total_detections")
        
        if detection.get('threat_detected'):
            await redis_client.incr("stats:threats_detected")
            
            # Update attack type stats
            attack_type = detection.get('attack_type', 'Unknown')
            await redis_client.hincrby("stats:attack_types", attack_type, 1)
            
            # Update severity distribution
            severity = detection.get('severity', 'UNKNOWN')
            await redis_client.hincrby("stats:severity_distribution", severity, 1)
        
        # Cache recent detection
        await redis_client.lpush(
            "recent_detections",
            json.dumps(detection)
        )
        await redis_client.ltrim("recent_detections", 0, 999)  # Keep last 1000
        
    except Exception as e:
        logger.error(f"Redis cache error: {e}")

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url)
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url)
        }
    )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=5000,
        reload=False,
        workers=4,
        log_level="info"
    )
