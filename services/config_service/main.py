"""
Cyber Sentinel ML - Configuration Service
Enterprise-grade configuration management microservice
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, generate_latest
from prometheus_fastapi_instrumentator import Instrumentator
import time
import logging
import asyncio
import asyncpg
import json
import yaml
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import uvicorn
import os
from contextlib import asynccontextmanager
from pydantic import BaseModel, Field
import redis.asyncio as redis

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus metrics
CONFIG_REQUESTS = Counter('config_service_requests_total', 'Total config requests', ['endpoint'])
CONFIG_DURATION = Histogram('config_service_duration_seconds', 'Config request duration')
CONFIG_UPDATES = Counter('config_updates_total', 'Total config updates', ['section'])

# Global variables
db_pool = None
redis_client = None

# Pydantic models
class SystemConfig(BaseModel):
    real_time_detection: bool = True
    auto_response: bool = False
    notification_email: str = ""
    log_level: str = "INFO"
    max_connections: int = 1000
    timeout: int = 30

class SecurityConfig(BaseModel):
    session_timeout: int = 3600
    max_login_attempts: int = 5
    password_policy: bool = True
    two_factor_auth: bool = False
    ip_whitelist: str = ""

class MLConfig(BaseModel):
    model_version: str = "v2.0.0"
    confidence_threshold: float = 0.8
    batch_size: int = 32
    gpu_acceleration: bool = True
    auto_retraining: bool = True

class AttackRule(BaseModel):
    id: str
    name: str
    category: str
    severity: str
    enabled: bool
    description: str
    detection_rules: List[str]
    auto_response: str
    confidence_threshold: float = 0.8

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("🚀 Starting Configuration Service...")
    
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
    
    # Initialize Redis
    global redis_client
    try:
        redis_client = redis.from_url(
            os.getenv('REDIS_URL', 'redis://localhost:6379'),
            decode_responses=True
        )
        await redis_client.ping()
        logger.info("✅ Redis connected")
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")
    
    # Initialize default configuration
    await initialize_default_config()
    
    logger.info("🎉 Configuration Service ready!")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Configuration Service...")
    if db_pool:
        await db_pool.close()
    if redis_client:
        await redis_client.close()
    logger.info("✅ Service shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="Cyber Sentinel - Configuration Service",
    description="Enterprise-grade configuration management microservice",
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

async def get_redis():
    return redis_client

# Helper functions
async def initialize_default_config():
    """Initialize default configuration in database"""
    try:
        if not db_pool:
            return
        
        async with db_pool.acquire() as conn:
            # Create config tables
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS system_config (
                    key VARCHAR(100) PRIMARY KEY,
                    value JSONB NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_by VARCHAR(100) DEFAULT 'system'
                )
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS attack_rules (
                    id VARCHAR(100) PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    category VARCHAR(100) NOT NULL,
                    severity VARCHAR(20) NOT NULL,
                    enabled BOOLEAN DEFAULT true,
                    description TEXT,
                    detection_rules JSONB,
                    auto_response VARCHAR(50),
                    confidence_threshold FLOAT DEFAULT 0.8,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insert default system config if not exists
            default_config = {
                "system": SystemConfig().dict(),
                "security": SecurityConfig().dict(),
                "ml": MLConfig().dict()
            }
            
            for section, config in default_config.items():
                await conn.execute("""
                    INSERT INTO system_config (key, value) 
                    VALUES ($1, $2)
                    ON CONFLICT (key) DO NOTHING
                """, section, config)
            
            logger.info("✅ Default configuration initialized")
            
    except Exception as e:
        logger.error(f"❌ Failed to initialize default config: {e}")

async def cache_config(section: str, config: Dict[str, Any]):
    """Cache configuration in Redis"""
    try:
        if redis_client:
            await redis_client.setex(
                f"config:{section}",
                3600,  # 1 hour TTL
                json.dumps(config)
            )
    except Exception as e:
        logger.error(f"Failed to cache config {section}: {e}")

async def get_cached_config(section: str) -> Optional[Dict[str, Any]]:
    """Get configuration from Redis cache"""
    try:
        if redis_client:
            cached = await redis_client.get(f"config:{section}")
            if cached:
                return json.loads(cached)
    except Exception as e:
        logger.error(f"Failed to get cached config {section}: {e}")
    return None

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
    
    status_code = 200 if health_status["status"] == "healthy" else 503
    return health_status

@app.get("/api/v1/config", tags=["Configuration"])
async def get_config(
    section: Optional[str] = None,
    use_cache: bool = True,
    db=Depends(get_db)
):
    """Get configuration"""
    try:
        if not db:
            raise HTTPException(status_code=503, detail="Database not available")
        
        result = {}
        
        if section:
            # Get specific section
            if use_cache:
                cached = await get_cached_config(section)
                if cached:
                    return cached
            
            async with db_pool.acquire() as conn:
                config_data = await conn.fetchrow(
                    "SELECT value FROM system_config WHERE key = $1",
                    section
                )
                
                if not config_data:
                    raise HTTPException(status_code=404, detail=f"Configuration section '{section}' not found")
                
                result = config_data['value']
                await cache_config(section, result)
        else:
            # Get all configuration
            async with db_pool.acquire() as conn:
                config_rows = await conn.fetch("SELECT key, value FROM system_config")
                result = {row['key']: row['value'] for row in config_rows}
                
                # Cache all sections
                for key, value in result.items():
                    await cache_config(key, value)
        
        CONFIG_REQUESTS.labels(endpoint="/config").inc()
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Config retrieval error: {e}")
        raise HTTPException(status_code=500, detail=f"Configuration retrieval failed: {str(e)}")

@app.put("/api/v1/config", tags=["Configuration"])
async def update_config(
    config_updates: Dict[str, Any],
    background_tasks: BackgroundTasks,
    db=Depends(get_db)
):
    """Update configuration"""
    try:
        if not db:
            raise HTTPException(status_code=503, detail="Database not available")
        
        updated_sections = []
        
        async with db_pool.acquire() as conn:
            async with conn.transaction():
                for section, config in config_updates.items():
                    # Validate configuration
                    if section == "system":
                        SystemConfig(**config)
                    elif section == "security":
                        SecurityConfig(**config)
                    elif section == "ml":
                        MLConfig(**config)
                    else:
                        raise HTTPException(status_code=400, detail=f"Unknown configuration section: {section}")
                    
                    # Update in database
                    await conn.execute("""
                        UPDATE system_config 
                        SET value = $1, updated_at = CURRENT_TIMESTAMP, updated_by = 'system'
                        WHERE key = $2
                    """, config, section)
                    
                    # Update cache
                    await cache_config(section, config)
                    updated_sections.append(section)
                    
                    CONFIG_UPDATES.labels(section=section).inc()
        
        # Notify other services of configuration change
        background_tasks.add_task(notify_config_change, updated_sections)
        
        return {
            "message": "Configuration updated successfully",
            "updated_sections": updated_sections,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Config update error: {e}")
        raise HTTPException(status_code=500, detail=f"Configuration update failed: {str(e)}")

async def notify_config_change(updated_sections: List[str]):
    """Notify other services of configuration changes"""
    try:
        if redis_client:
            message = {
                "type": "config_update",
                "sections": updated_sections,
                "timestamp": datetime.utcnow().isoformat()
            }
            await redis_client.publish("config_updates", json.dumps(message))
            logger.info(f"Config change notification sent for sections: {updated_sections}")
    except Exception as e:
        logger.error(f"Failed to notify config change: {e}")

@app.get("/api/v1/config/attack-rules", tags=["Attack Rules"])
async def get_attack_rules(
    enabled_only: bool = False,
    category: Optional[str] = None,
    db=Depends(get_db)
):
    """Get attack detection rules"""
    try:
        if not db:
            raise HTTPException(status_code=503, detail="Database not available")
        
        async with db_pool.acquire() as conn:
            query = "SELECT * FROM attack_rules"
            conditions = []
            params = []
            
            if enabled_only:
                conditions.append("enabled = true")
            
            if category:
                conditions.append("category = $1")
                params.append(category)
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY category, name"
            
            rules = await conn.fetch(query, *params)
        
        return {
            "rules": [dict(rule) for rule in rules],
            "total_count": len(rules)
        }
        
    except Exception as e:
        logger.error(f"Attack rules retrieval error: {e}")
        raise HTTPException(status_code=500, detail=f"Attack rules retrieval failed: {str(e)}")

@app.post("/api/v1/config/attack-rules", tags=["Attack Rules"])
async def create_attack_rule(
    rule: AttackRule,
    db=Depends(get_db)
):
    """Create new attack rule"""
    try:
        if not db:
            raise HTTPException(status_code=503, detail="Database not available")
        
        async with db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO attack_rules 
                (id, name, category, severity, enabled, description, detection_rules, auto_response, confidence_threshold)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """, 
            rule.id, rule.name, rule.category, rule.severity, rule.enabled,
            rule.description, json.dumps(rule.detection_rules), rule.auto_response, rule.confidence_threshold
            )
        
        return {
            "message": "Attack rule created successfully",
            "rule_id": rule.id
        }
        
    except Exception as e:
        logger.error(f"Attack rule creation error: {e}")
        raise HTTPException(status_code=500, detail=f"Attack rule creation failed: {str(e)}")

@app.put("/api/v1/config/attack-rules/{rule_id}", tags=["Attack Rules"])
async def update_attack_rule(
    rule_id: str,
    rule_update: Dict[str, Any],
    db=Depends(get_db)
):
    """Update attack rule"""
    try:
        if not db:
            raise HTTPException(status_code=503, detail="Database not available")
        
        # Build update query dynamically
        update_fields = []
        params = []
        param_index = 1
        
        for field, value in rule_update.items():
            if field in ['name', 'category', 'severity', 'enabled', 'description', 'auto_response', 'confidence_threshold']:
                update_fields.append(f"{field} = ${param_index}")
                params.append(value)
                param_index += 1
            elif field == 'detection_rules':
                update_fields.append(f"detection_rules = ${param_index}")
                params.append(json.dumps(value))
                param_index += 1
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No valid fields to update")
        
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        params.append(rule_id)
        
        async with db_pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE attack_rules 
                SET {0}
                WHERE id = ${1}
            """.format(", ".join(update_fields)), *params)
        
        return {
            "message": "Attack rule updated successfully",
            "rule_id": rule_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Attack rule update error: {e}")
        raise HTTPException(status_code=500, detail=f"Attack rule update failed: {str(e)}")

@app.delete("/api/v1/config/attack-rules/{rule_id}", tags=["Attack Rules"])
async def delete_attack_rule(
    rule_id: str,
    db=Depends(get_db)
):
    """Delete attack rule"""
    try:
        if not db:
            raise HTTPException(status_code=503, detail="Database not available")
        
        async with db_pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM attack_rules WHERE id = $1",
                rule_id
            )
        
        return {
            "message": "Attack rule deleted successfully",
            "rule_id": rule_id
        }
        
    except Exception as e:
        logger.error(f"Attack rule deletion error: {e}")
        raise HTTPException(status_code=500, detail=f"Attack rule deletion failed: {str(e)}")

@app.post("/api/v1/config/attack-rules/{rule_id}/enable", tags=["Attack Rules"])
async def enable_attack_rule(
    rule_id: str,
    db=Depends(get_db)
):
    """Enable attack rule"""
    return await update_attack_rule(rule_id, {"enabled": True}, db)

@app.post("/api/v1/config/attack-rules/{rule_id}/disable", tags=["Attack Rules"])
async def disable_attack_rule(
    rule_id: str,
    db=Depends(get_db)
):
    """Disable attack rule"""
    return await update_attack_rule(rule_id, {"enabled": False}, db)

@app.get("/api/v1/config/attack-rules/{rule_id}", tags=["Attack Rules"])
async def get_attack_rule(
    rule_id: str,
    db=Depends(get_db)
):
    """Get specific attack rule"""
    try:
        if not db:
            raise HTTPException(status_code=503, detail="Database not available")
        
        async with db_pool.acquire() as conn:
            rule = await conn.fetchrow(
                "SELECT * FROM attack_rules WHERE id = $1",
                rule_id
            )
        
        if not rule:
            raise HTTPException(status_code=404, detail=f"Attack rule '{rule_id}' not found")
        
        return dict(rule)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Attack rule retrieval error: {e}")
        raise HTTPException(status_code=500, detail=f"Attack rule retrieval failed: {str(e)}")

@app.get("/api/v1/config/export", tags=["Configuration"])
async def export_config(
    format: str = "json",
    db=Depends(get_db)
):
    """Export configuration"""
    try:
        if not db:
            raise HTTPException(status_code=503, detail="Database not available")
        
        async with db_pool.acquire() as conn:
            config_rows = await conn.fetch("SELECT key, value FROM system_config")
            config_data = {row['key']: row['value'] for row in config_rows}
            
            rules_rows = await conn.fetch("SELECT * FROM attack_rules")
            rules_data = [dict(rule) for rule in rules_rows]
        
        export_data = {
            "config": config_data,
            "attack_rules": rules_data,
            "exported_at": datetime.utcnow().isoformat(),
            "version": "2.0.0"
        }
        
        if format == "json":
            return export_data
        elif format == "yaml":
            return yaml.dump(export_data, default_flow_style=False)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported export format: {format}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Config export error: {e}")
        raise HTTPException(status_code=500, detail=f"Configuration export failed: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=7000,
        reload=False,
        workers=4,
        log_level="info"
    )
