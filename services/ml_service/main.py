"""
Cyber Sentinel ML - Model Service
Enterprise-grade ML model serving microservice
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, generate_latest
from prometheus_fastapi_instrumentator import Instrumentator
import time
import logging
import asyncio
import aioredis
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
import uvicorn
import os
from datetime import datetime
import json
import pickle
from contextlib import asynccontextmanager

# Import ML components
try:
    import tensorflow as tf
    from tensorflow.keras.models import load_model
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False

try:
    import torch
    import torch.nn as nn
    PYTORCH_AVAILABLE = True
except ImportError:
    PYTORCH_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus metrics
MODEL_REQUESTS = Counter('ml_service_model_requests_total', 'Total model requests', ['model_name'])
MODEL_INFERENCE_TIME = Histogram('ml_service_inference_duration_seconds', 'Model inference duration', ['model_name'])
MODEL_ACCURACY = Histogram('ml_service_model_accuracy', 'Model accuracy', ['model_name'])
ACTIVE_MODELS = Gauge('ml_service_active_models', 'Number of active models')

# Global variables
redis_client = None
models = {}
model_metadata = {}

class ModelManager:
    """Enterprise model management"""
    
    def __init__(self):
        self.models = {}
        self.metadata = {}
        self.model_versions = {}
    
    async def load_model(self, model_name: str, model_path: str, model_type: str = "tensorflow"):
        """Load ML model with versioning"""
        try:
            if model_type == "tensorflow" and TENSORFLOW_AVAILABLE:
                model = load_model(model_path)
            elif model_type == "pytorch" and PYTORCH_AVAILABLE:
                model = torch.load(model_path)
            else:
                raise ValueError(f"Unsupported model type: {model_type}")
            
            version = int(time.time())
            self.models[model_name] = model
            self.model_versions[model_name] = version
            self.metadata[model_name] = {
                "type": model_type,
                "path": model_path,
                "version": version,
                "loaded_at": datetime.utcnow().isoformat(),
                "status": "active"
            }
            
            ACTIVE_MODELS.set(len(self.models))
            logger.info(f"✅ Model {model_name} loaded successfully (version {version})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to load model {model_name}: {e}")
            return False
    
    def get_model(self, model_name: str):
        """Get model by name"""
        if model_name not in self.models:
            raise ValueError(f"Model {model_name} not found")
        return self.models[model_name]
    
    def get_model_metadata(self, model_name: str):
        """Get model metadata"""
        return self.metadata.get(model_name, {})
    
    def list_models(self):
        """List all loaded models"""
        return list(self.models.keys())
    
    async def unload_model(self, model_name: str):
        """Unload model"""
        if model_name in self.models:
            del self.models[model_name]
            del self.metadata[model_name]
            del self.model_versions[model_name]
            ACTIVE_MODELS.set(len(self.models))
            logger.info(f"🗑️ Model {model_name} unloaded")

class ThreatClassifier:
    """Enterprise threat classification"""
    
    def __init__(self, model_manager: ModelManager):
        self.model_manager = model_manager
        self.scaler = None
        self.label_encoder = None
        self.feature_columns = []
    
    async def load_preprocessors(self, scaler_path: str, encoder_path: str):
        """Load preprocessing components"""
        try:
            if os.path.exists(scaler_path):
                with open(scaler_path, 'rb') as f:
                    self.scaler = pickle.load(f)
                logger.info("✅ Scaler loaded")
            
            if os.path.exists(encoder_path):
                with open(encoder_path, 'rb') as f:
                    self.label_encoder = pickle.load(f)
                logger.info("✅ Label encoder loaded")
                
        except Exception as e:
            logger.error(f"❌ Failed to load preprocessors: {e}")
    
    def preprocess_features(self, packet_data: Dict[str, Any]) -> np.ndarray:
        """Preprocess packet features"""
        try:
            # Extract features from packet data
            features = []
            
            # Basic features
            features.append(int(packet_data.get('src_port', 0)))
            features.append(int(packet_data.get('dst_port', 0)))
            features.append(len(packet_data.get('srcip', '')))
            features.append(len(packet_data.get('dstip', '')))
            features.append(1 if packet_data.get('protocol') == 'TCP' else 0)
            features.append(1 if packet_data.get('protocol') == 'UDP' else 0)
            features.append(1 if packet_data.get('protocol') == 'ICMP' else 0)
            features.append(int(packet_data.get('packet_size', 0)))
            features.append(float(packet_data.get('duration', 0)))
            
            # TCP flags
            flags = packet_data.get('flags', 0)
            features.append(1 if flags & 0x02 else 0)  # SYN
            features.append(1 if flags & 0x10 else 0)  # ACK
            features.append(1 if flags & 0x01 else 0)  # FIN
            features.append(1 if flags & 0x04 else 0)  # RST
            
            # Time-based features
            if 'timestamp' in packet_data:
                timestamp = datetime.fromisoformat(packet_data['timestamp'].replace('Z', '+00:00'))
                features.append(timestamp.hour)
                features.append(timestamp.weekday())
            else:
                features.extend([0, 0])
            
            features_array = np.array(features).reshape(1, -1)
            
            # Apply scaling if available
            if self.scaler:
                features_array = self.scaler.transform(features_array)
            
            return features_array
            
        except Exception as e:
            logger.error(f"Feature preprocessing error: {e}")
            raise
    
    async def classify(self, packet_data: Dict[str, Any], model_name: str = "cyber_sentinel_model") -> Dict[str, Any]:
        """Classify packet as threat or normal"""
        try:
            # Get model
            model = self.model_manager.get_model(model_name)
            
            # Preprocess features
            features = self.preprocess_features(packet_data)
            
            # Make prediction
            start_time = time.time()
            
            if isinstance(model, tf.keras.Model):
                prediction = model.predict(features, verbose=0)
                predicted_class = np.argmax(prediction[0])
                confidence = float(np.max(prediction[0]))
            else:
                with torch.no_grad():
                    features_tensor = torch.FloatTensor(features)
                    prediction = model(features_tensor)
                    predicted_class = torch.argmax(prediction, dim=1).item()
                    confidence = float(torch.max(torch.softmax(prediction, dim=1)))
            
            inference_time = time.time() - start_time
            MODEL_INFERENCE_TIME.labels(model_name=model_name).observe(inference_time)
            
            # Map class to label
            if self.label_encoder:
                try:
                    attack_type = self.label_encoder.inverse_transform([predicted_class])[0]
                except:
                    attack_type = f"CLASS_{predicted_class}"
            else:
                attack_type = f"CLASS_{predicted_class}"
            
            # Determine severity based on attack type and confidence
            severity = "LOW"
            if confidence > 0.8:
                severity = "HIGH"
            elif confidence > 0.6:
                severity = "MEDIUM"
            
            # Map common attack types
            threat_detected = attack_type != "BENIGN"
            
            result = {
                "threat_detected": threat_detected,
                "attack_type": attack_type,
                "confidence": confidence,
                "severity": severity,
                "predicted_class": int(predicted_class),
                "inference_time": inference_time,
                "model_name": model_name,
                "model_version": self.model_manager.model_versions.get(model_name, 0),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            MODEL_REQUESTS.labels(model_name=model_name).inc()
            
            return result
            
        except Exception as e:
            logger.error(f"Classification error: {e}")
            return {
                "error": str(e),
                "threat_detected": False,
                "attack_type": "ERROR",
                "confidence": 0.0,
                "severity": "UNKNOWN"
            }

# Global instances
model_manager = ModelManager()
classifier = ThreatClassifier(model_manager)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("🚀 Starting ML Model Service...")
    
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
    
    # Load models
    model_path = os.getenv('MODEL_PATH', './models')
    
    # Load main classification model
    main_model_path = os.path.join(model_path, 'CICIDS2017_5class_model.h5')
    if os.path.exists(main_model_path):
        await model_manager.load_model("cyber_sentinel_model", main_model_path, "tensorflow")
    
    # Load preprocessors
    scaler_path = os.path.join(model_path, 'scaler.pkl')
    encoder_path = os.path.join(model_path, 'label_encoder.pkl')
    await classifier.load_preprocessors(scaler_path, encoder_path)
    
    logger.info("🎉 ML Model Service ready!")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down ML Model Service...")
    if redis_client:
        await redis_client.close()
    logger.info("✅ Service shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="Cyber Sentinel - ML Model Service",
    description="Enterprise-grade ML model serving microservice",
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

# API endpoints
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0",
        "models_loaded": len(model_manager.models),
        "tensorflow_available": TENSORFLOW_AVAILABLE,
        "pytorch_available": PYTORCH_AVAILABLE,
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
    
    status_code = 200 if health_status["status"] == "healthy" else 503
    return health_status

@app.post("/api/v1/ml/classify", tags=["ML Inference"])
async def classify_packet(packet_data: Dict[str, Any]):
    """
    Classify network packet as threat or normal
    """
    try:
        result = await classifier.classify(packet_data)
        return result
        
    except Exception as e:
        logger.error(f"Classification error: {e}")
        raise HTTPException(status_code=500, detail=f"Classification failed: {str(e)}")

@app.post("/api/v1/ml/batch-classify", tags=["ML Inference"])
async def batch_classify_packets(packets_data: Dict[str, Any]):
    """
    Batch classify multiple packets
    """
    try:
        packets = packets_data.get('packets', [])
        
        if not packets:
            raise HTTPException(status_code=400, detail="No packets provided")
        
        if len(packets) > 50:
            raise HTTPException(status_code=400, detail="Too many packets (max 50)")
        
        results = []
        for packet in packets:
            try:
                result = await classifier.classify(packet)
                results.append(result)
            except Exception as e:
                results.append({
                    "error": str(e),
                    "threat_detected": False,
                    "attack_type": "ERROR"
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
        logger.error(f"Batch classification error: {e}")
        raise HTTPException(status_code=500, detail=f"Batch classification failed: {str(e)}")

@app.get("/api/v1/ml/models", tags=["Model Management"])
async def list_models():
    """List all loaded models"""
    try:
        models_info = {}
        for model_name in model_manager.list_models():
            models_info[model_name] = model_manager.get_model_metadata(model_name)
        
        return {
            "total_models": len(models_info),
            "models": models_info
        }
        
    except Exception as e:
        logger.error(f"Model listing error: {e}")
        raise HTTPException(status_code=500, detail=f"Model listing failed: {str(e)}")

@app.get("/api/v1/ml/models/{model_name}", tags=["Model Management"])
async def get_model_info(model_name: str):
    """Get detailed information about a specific model"""
    try:
        metadata = model_manager.get_model_metadata(model_name)
        if not metadata:
            raise HTTPException(status_code=404, detail=f"Model {model_name} not found")
        
        return metadata
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Model info error: {e}")
        raise HTTPException(status_code=500, detail=f"Model info retrieval failed: {str(e)}")

@app.post("/api/v1/ml/models/{model_name}/reload", tags=["Model Management"])
async def reload_model(model_name: str):
    """Reload a specific model"""
    try:
        metadata = model_manager.get_model_metadata(model_name)
        if not metadata:
            raise HTTPException(status_code=404, detail=f"Model {model_name} not found")
        
        success = await model_manager.load_model(
            model_name, 
            metadata["path"], 
            metadata["type"]
        )
        
        if success:
            return {"message": f"Model {model_name} reloaded successfully"}
        else:
            raise HTTPException(status_code=500, detail="Model reload failed")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Model reload error: {e}")
        raise HTTPException(status_code=500, detail=f"Model reload failed: {str(e)}")

@app.delete("/api/v1/ml/models/{model_name}", tags=["Model Management"])
async def unload_model(model_name: str):
    """Unload a specific model"""
    try:
        await model_manager.unload_model(model_name)
        return {"message": f"Model {model_name} unloaded successfully"}
        
    except Exception as e:
        logger.error(f"Model unload error: {e}")
        raise HTTPException(status_code=500, detail=f"Model unload failed: {str(e)}")

@app.get("/api/v1/ml/stats", tags=["Analytics"])
async def get_ml_stats():
    """Get ML service statistics"""
    try:
        stats = {
            "timestamp": datetime.utcnow().isoformat(),
            "active_models": len(model_manager.models),
            "tensorflow_available": TENSORFLOW_AVAILABLE,
            "pytorch_available": PYTORCH_AVAILABLE,
            "redis_connected": redis_client is not None
        }
        
        # Get model-specific stats from Redis
        if redis_client:
            try:
                model_stats = await redis_client.hgetall("ml_model_stats")
                stats["model_stats"] = {k: json.loads(v) for k, v in model_stats.items()}
            except Exception as e:
                logger.error(f"Redis stats error: {e}")
        
        return stats
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail=f"Stats retrieval failed: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=9999,
        reload=False,
        workers=2,
        log_level="info"
    )
