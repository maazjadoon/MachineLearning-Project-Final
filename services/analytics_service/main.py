"""
Cyber Sentinel ML - Analytics Service
Enterprise-grade analytics and reporting microservice
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, generate_latest
from prometheus_fastapi_instrumentator import Instrumentator
import time
import logging
import asyncio
import asyncpg
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import uvicorn
import os
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus metrics
ANALYTICS_REQUESTS = Counter('analytics_service_requests_total', 'Total analytics requests', ['endpoint'])
ANALYTICS_DURATION = Histogram('analytics_service_duration_seconds', 'Analytics request duration')
REPORT_GENERATION = Counter('report_generation_total', 'Total reports generated', ['format'])

# Global variables
db_pool = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("🚀 Starting Analytics Service...")
    
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
    
    logger.info("🎉 Analytics Service ready!")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Analytics Service...")
    if db_pool:
        await db_pool.close()
    logger.info("✅ Service shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="Cyber Sentinel - Analytics Service",
    description="Enterprise-grade analytics and reporting microservice",
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

# Prometheus instrumentation
Instrumentator().instrument(app).expose(app)

# Dependencies
async def get_db():
    return db_pool

# API endpoints
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0",
        "services": {}
    }
    
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
    
    status_code = 200 if health_status["status"] == "healthy" else 503
    return health_status

@app.get("/api/v1/analytics", tags=["Analytics"])
async def get_analytics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    attack_type: Optional[str] = None,
    severity: Optional[str] = None,
    db=Depends(get_db)
):
    """Get comprehensive analytics data"""
    try:
        if not db:
            raise HTTPException(status_code=503, detail="Database not available")
        
        # Parse date range
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        else:
            start_dt = datetime.utcnow() - timedelta(days=7)
        
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        else:
            end_dt = datetime.utcnow()
        
        async with db_pool.acquire() as conn:
            # Get time series data
            time_series_query = """
                SELECT 
                    DATE_TRUNC('hour', timestamp) as hour,
                    COUNT(*) as total_detections,
                    COUNT(*) FILTER (WHERE threat_detected = true) as threats_detected,
                    AVG(confidence) as avg_confidence
                FROM threat_detections
                WHERE timestamp BETWEEN $1 AND $2
                GROUP BY DATE_TRUNC('hour', timestamp)
                ORDER BY hour
            """
            time_series_data = await conn.fetch(time_series_query, start_dt, end_dt)
            
            # Get attack type distribution
            attack_type_query = """
                SELECT attack_type, COUNT(*) as count
                FROM threat_detections
                WHERE timestamp BETWEEN $1 AND $2 AND threat_detected = true
                GROUP BY attack_type
                ORDER BY count DESC
            """
            if attack_type:
                attack_type_query = attack_type_query.replace("WHERE", f"WHERE attack_type = '{attack_type}' AND")
            
            attack_type_data = await conn.fetch(attack_type_query, start_dt, end_dt)
            
            # Get severity distribution
            severity_query = """
                SELECT severity, COUNT(*) as count
                FROM threat_detections
                WHERE timestamp BETWEEN $1 AND $2 AND threat_detected = true
                GROUP BY severity
                ORDER BY count DESC
            """
            if severity:
                severity_query = severity_query.replace("WHERE", f"WHERE severity = '{severity}' AND")
            
            severity_data = await conn.fetch(severity_query, start_dt, end_dt)
            
            # Get top source IPs
            top_ips_query = """
                SELECT source_ip, COUNT(*) as count
                FROM threat_detections
                WHERE timestamp BETWEEN $1 AND $2 AND threat_detected = true
                GROUP BY source_ip
                ORDER BY count DESC
                LIMIT 10
            """
            top_ips_data = await conn.fetch(top_ips_query, start_dt, end_dt)
            
            # Get key metrics
            metrics_query = """
                SELECT 
                    COUNT(*) as total_detections,
                    COUNT(*) FILTER (WHERE threat_detected = true) as threats_detected,
                    AVG(confidence) as avg_confidence,
                    MAX(timestamp) as last_detection
                FROM threat_detections
                WHERE timestamp BETWEEN $1 AND $2
            """
            metrics_data = await conn.fetchrow(metrics_query, start_dt, end_dt)
        
        # Format response
        analytics_data = {
            "time_range": {
                "start": start_dt.isoformat(),
                "end": end_dt.isoformat()
            },
            "time_series": [
                {
                    "timestamp": row["hour"].isoformat(),
                    "total_detections": row["total_detections"],
                    "threats_detected": row["threats_detected"],
                    "avg_confidence": float(row["avg_confidence"]) if row["avg_confidence"] else 0
                }
                for row in time_series_data
            ],
            "attack_types": [
                {
                    "type": row["attack_type"] or "Unknown",
                    "count": row["count"]
                }
                for row in attack_type_data
            ],
            "severity_distribution": [
                {
                    "severity": row["severity"],
                    "count": row["count"]
                }
                for row in severity_data
            ],
            "top_source_ips": [
                {
                    "ip": row["source_ip"],
                    "count": row["count"]
                }
                for row in top_ips_data
            ],
            "metrics": {
                "total_detections": metrics_data["total_detections"],
                "threats_detected": metrics_data["threats_detected"],
                "detection_rate": (
                    metrics_data["threats_detected"] / metrics_data["total_detections"] * 100
                    if metrics_data["total_detections"] > 0 else 0
                ),
                "avg_confidence": float(metrics_data["avg_confidence"]) if metrics_data["avg_confidence"] else 0,
                "last_detection": metrics_data["last_detection"].isoformat() if metrics_data["last_detection"] else None
            }
        }
        
        ANALYTICS_REQUESTS.labels(endpoint="/analytics").inc()
        return analytics_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analytics error: {e}")
        raise HTTPException(status_code=500, detail=f"Analytics retrieval failed: {str(e)}")

@app.get("/api/v1/analytics/reports", tags=["Analytics"])
async def get_reports(
    limit: int = 50,
    offset: int = 0,
    db=Depends(get_db)
):
    """Get generated reports list"""
    try:
        if not db:
            raise HTTPException(status_code=503, detail="Database not available")
        
        async with db_pool.acquire() as conn:
            # Ensure reports table exists
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS analytics_reports (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    type VARCHAR(50) NOT NULL,
                    format VARCHAR(20) NOT NULL,
                    parameters JSONB,
                    file_path VARCHAR(500),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by VARCHAR(100),
                    file_size BIGINT,
                    status VARCHAR(20) DEFAULT 'completed'
                )
            """)
            
            # Get reports
            query = """
                SELECT * FROM analytics_reports
                ORDER BY created_at DESC
                LIMIT $1 OFFSET $2
            """
            reports = await conn.fetch(query, limit, offset)
            
            # Get total count
            count_query = "SELECT COUNT(*) FROM analytics_reports"
            total_count = await conn.fetchval(count_query)
        
        return {
            "reports": [dict(report) for report in reports],
            "total_count": total_count,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Reports error: {e}")
        raise HTTPException(status_code=500, detail=f"Reports retrieval failed: {str(e)}")

@app.post("/api/v1/analytics/reports", tags=["Analytics"])
async def generate_report(
    report_config: Dict[str, Any],
    background_tasks: BackgroundTasks,
    db=Depends(get_db)
):
    """Generate analytics report"""
    try:
        report_type = report_config.get('type', 'summary')
        format_type = report_config.get('format', 'pdf')
        time_range = report_config.get('time_range', {})
        
        # Validate report type
        valid_types = ['summary', 'detailed', 'threats', 'performance']
        if report_type not in valid_types:
            raise HTTPException(status_code=400, detail=f"Invalid report type: {report_type}")
        
        # Validate format
        valid_formats = ['pdf', 'csv', 'xlsx']
        if format_type not in valid_formats:
            raise HTTPException(status_code=400, detail=f"Invalid format: {format_type}")
        
        if not db:
            raise HTTPException(status_code=503, detail="Database not available")
        
        # Create report record
        async with db_pool.acquire() as conn:
            report_id = await conn.fetchval("""
                INSERT INTO analytics_reports (name, type, format, parameters, created_by)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
            """, 
            f"{report_type.title()} Report",
            report_type,
            format_type,
            report_config,
            "system"
            )
        
        # Generate report in background
        background_tasks.add_task(generate_report_file, report_id, report_config)
        
        REPORT_GENERATION.labels(format=format_type).inc()
        
        return {
            "report_id": report_id,
            "message": "Report generation started",
            "estimated_time": "2-5 minutes"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Report generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")

async def generate_report_file(report_id: int, config: Dict[str, Any]):
    """Generate report file in background"""
    try:
        # This would integrate with a report generation service
        # For now, we'll just mark it as completed
        if db_pool:
            async with db_pool.acquire() as conn:
                await conn.execute("""
                    UPDATE analytics_reports 
                    SET status = 'completed', file_size = 1024
                    WHERE id = $1
                """, report_id)
        
        logger.info(f"Report {report_id} generated successfully")
        
    except Exception as e:
        logger.error(f"Report generation failed for {report_id}: {e}")
        if db_pool:
            async with db_pool.acquire() as conn:
                await conn.execute("""
                    UPDATE analytics_reports 
                    SET status = 'failed'
                    WHERE id = $1
                """, report_id)

@app.get("/api/v1/analytics/performance", tags=["Analytics"])
async def get_performance_metrics(
    time_range: str = "24h",
    db=Depends(get_db)
):
    """Get performance metrics"""
    try:
        # Parse time range
        if time_range == "1h":
            start_dt = datetime.utcnow() - timedelta(hours=1)
        elif time_range == "24h":
            start_dt = datetime.utcnow() - timedelta(days=1)
        elif time_range == "7d":
            start_dt = datetime.utcnow() - timedelta(days=7)
        elif time_range == "30d":
            start_dt = datetime.utcnow() - timedelta(days=30)
        else:
            start_dt = datetime.utcnow() - timedelta(days=1)
        
        if not db:
            raise HTTPException(status_code=503, detail="Database not available")
        
        async with db_pool.acquire() as conn:
            # Get performance metrics
            performance_query = """
                SELECT 
                    DATE_TRUNC('minute', timestamp) as minute,
                    AVG(EXTRACT(EPOCH FROM (response_time))) as avg_response_time,
                    COUNT(*) as request_count,
                    COUNT(*) FILTER (WHERE threat_detected = true) as threat_count
                FROM threat_detections
                WHERE timestamp >= $1
                GROUP BY DATE_TRUNC('minute', timestamp)
                ORDER BY minute DESC
                LIMIT 100
            """
            performance_data = await conn.fetch(performance_query, start_dt)
        
        return {
            "time_range": time_range,
            "metrics": [
                {
                    "timestamp": row["minute"].isoformat(),
                    "avg_response_time": float(row["avg_response_time"]) if row["avg_response_time"] else 0,
                    "request_count": row["request_count"],
                    "threat_count": row["threat_count"]
                }
                for row in performance_data
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Performance metrics error: {e}")
        raise HTTPException(status_code=500, detail=f"Performance metrics failed: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=6000,
        reload=False,
        workers=4,
        log_level="info"
    )
