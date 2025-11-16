"""
Configuration settings for Cyber Sentinel ML Project
Controls whether the system runs in production (real threats) or test mode (simulated threats)
"""

import os
from typing import Dict, Any

class Config:
    """Configuration class for Cyber Sentinel"""
    
    # Mode Configuration
    PRODUCTION_MODE = os.environ.get('CYBER_SENTINEL_PRODUCTION', 'true').lower() == 'true'
    
    # Logging Configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO' if PRODUCTION_MODE else 'DEBUG')
    
    # Packet Capture Configuration
    PACKET_CAPTURE_ENABLED = os.environ.get('PACKET_CAPTURE_ENABLED', 'true' if PRODUCTION_MODE else 'false').lower() == 'true'
    MAX_PACKETS_PER_SECOND = int(os.environ.get('MAX_PACKETS_PER_SECOND', '50' if PRODUCTION_MODE else '100'))
    
    # Model Server Configuration
    MODEL_SERVER_HOST = os.environ.get('MODEL_SERVER_HOST', 'localhost')
    MODEL_SERVER_PORT = int(os.environ.get('MODEL_SERVER_PORT', '9999'))
    
    # Web Application Configuration
    WEB_HOST = os.environ.get('WEB_HOST', '0.0.0.0')
    WEB_PORT = int(os.environ.get('WEB_PORT', '5000'))
    DEBUG_MODE = not PRODUCTION_MODE  # Debug mode only in test mode
    
    # Security Configuration
    RATE_LIMITING_ENABLED = PRODUCTION_MODE
    THREAT_RATE_LIMIT_SECONDS = int(os.environ.get('THREAT_RATE_LIMIT_SECONDS', '5'))
    
    # Test/Simulation Configuration
    SAMPLE_TRAFFIC_ENABLED = not PRODUCTION_MODE  # Only in test mode
    TEST_ENDPOINTS_ENABLED = True  # Available in both modes but clearly marked
    
    @classmethod
    def get_mode_info(cls) -> Dict[str, Any]:
        """Get current mode information"""
        return {
            'mode': 'PRODUCTION' if cls.PRODUCTION_MODE else 'TEST/DEVELOPMENT',
            'real_threat_detection': cls.PRODUCTION_MODE,
            'packet_capture_active': cls.PACKET_CAPTURE_ENABLED,
            'sample_traffic_active': cls.SAMPLE_TRAFFIC_ENABLED,
            'debug_mode': cls.DEBUG_MODE,
            'rate_limiting': cls.RATE_LIMITING_ENABLED
        }
    
    @classmethod
    def validate_production_requirements(cls) -> Dict[str, bool]:
        """Validate that production requirements are met"""
        requirements = {
            'scapy_available': False,
            'admin_privileges': False,  # This would need runtime check
            'model_server_running': False,  # This would need runtime check
            'proper_interface': False  # This would need runtime check
        }
        
        # Check if Scapy is available
        try:
            import scapy
            requirements['scapy_available'] = True
        except ImportError:
            pass
        
        return requirements

# Environment-specific configurations
class ProductionConfig(Config):
    """Production configuration"""
    PRODUCTION_MODE = True
    LOG_LEVEL = 'INFO'
    PACKET_CAPTURE_ENABLED = True
    SAMPLE_TRAFFIC_ENABLED = False
    DEBUG_MODE = False
    RATE_LIMITING_ENABLED = True

class DevelopmentConfig(Config):
    """Development configuration"""
    PRODUCTION_MODE = False
    LOG_LEVEL = 'DEBUG'
    PACKET_CAPTURE_ENABLED = False
    SAMPLE_TRAFFIC_ENABLED = True
    DEBUG_MODE = True
    RATE_LIMITING_ENABLED = False

class TestConfig(Config):
    """Test configuration"""
    PRODUCTION_MODE = False
    LOG_LEVEL = 'DEBUG'
    PACKET_CAPTURE_ENABLED = False
    SAMPLE_TRAFFIC_ENABLED = True
    DEBUG_MODE = True
    RATE_LIMITING_ENABLED = False

# Configuration mapping
config_map = {
    'production': ProductionConfig,
    'development': DevelopmentConfig,
    'test': TestConfig,
    'default': Config
}

def get_config(config_name: str = None) -> Config:
    """Get configuration by name"""
    if config_name is None:
        config_name = os.environ.get('CYBER_SENTINEL_ENV', 'default')
    
    return config_map.get(config_name, Config)()
