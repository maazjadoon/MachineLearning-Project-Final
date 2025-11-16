// API Configuration
export const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
export const SOCKET_URL = process.env.REACT_APP_SOCKET_URL || 'http://localhost:8000';

// WebSocket Configuration
export const WEBSOCKET_CONFIG = {
  transports: ['websocket', 'polling'] as const,
  timeout: 20000,
  forceNew: true,
  reconnection: true,
  reconnectionAttempts: 5,
  reconnectionDelay: 1000,
};

// Application Configuration
export const APP_CONFIG = {
  name: 'Cyber Sentinel ML',
  version: '2.0.0',
  description: 'Enterprise-grade network threat detection',
};

// UI Configuration
export const UI_CONFIG = {
  theme: {
    default: 'light' as const,
    colors: {
      primary: '#1890ff',
      success: '#52c41a',
      warning: '#faad14',
      error: '#ff4d4f',
      info: '#13c2c2',
    },
  },
  layout: {
    sidebarWidth: 250,
    headerHeight: 64,
    contentPadding: 24,
  },
  pagination: {
    defaultPageSize: 10,
    pageSizeOptions: ['10', '20', '50', '100'],
  },
};

// Monitoring Configuration
export const MONITORING_CONFIG = {
  metrics: {
    refreshInterval: 5000, // 5 seconds
    historyRetention: 1000, // Keep last 1000 data points
  },
  alerts: {
    thresholds: {
      threatRate: 100, // threats per minute
      errorRate: 5, // percentage
      latency: 1000, // milliseconds
    },
  },
};

// Security Configuration
export const SECURITY_CONFIG = {
  session: {
    timeout: 3600000, // 1 hour in milliseconds
    refreshThreshold: 300000, // 5 minutes before expiry
  },
  auth: {
    tokenKey: 'auth_token',
    refreshTokenKey: 'refresh_token',
  },
  csrf: {
    enabled: true,
    tokenHeader: 'X-CSRF-Token',
  },
};

// Feature Flags
export const FEATURE_FLAGS = {
  realTimeDetection: process.env.REACT_APP_FEATURE_REAL_TIME === 'true',
  advancedAnalytics: process.env.REACT_APP_FEATURE_ANALYTICS === 'true',
  mlModelV2: process.env.REACT_APP_FEATURE_ML_V2 === 'true',
  betaFeatures: process.env.REACT_APP_ENVIRONMENT === 'development',
};

// Environment Configuration
export const ENV_CONFIG = {
  isDevelopment: process.env.NODE_ENV === 'development',
  isProduction: process.env.NODE_ENV === 'production',
  isTest: process.env.NODE_ENV === 'test',
};

// Cache Configuration
export const CACHE_CONFIG = {
  api: {
    defaultTTL: 300000, // 5 minutes
    maxSize: 100, // Maximum number of cached items
  },
  static: {
    version: process.env.REACT_APP_CACHE_VERSION || '1.0.0',
  },
};

// Performance Configuration
export const PERFORMANCE_CONFIG = {
  bundle: {
    enabled: process.env.NODE_ENV === 'production',
    analyzer: process.env.REACT_APP_ANALYZE_BUNDLE === 'true',
  },
  lazyLoading: {
    enabled: true,
    threshold: 200, // pixels
  },
  imageOptimization: {
    enabled: true,
    quality: 85,
    placeholder: 'blur',
  },
};

// Error Configuration
export const ERROR_CONFIG = {
  reporting: {
    enabled: process.env.REACT_APP_ERROR_REPORTING === 'true',
    endpoint: process.env.REACT_APP_ERROR_ENDPOINT,
  },
  fallback: {
    retryAttempts: 3,
    retryDelay: 1000,
  },
};

// Export all configurations
export const CONFIG = {
  api: API_BASE_URL,
  socket: SOCKET_URL,
  websocket: WEBSOCKET_CONFIG,
  app: APP_CONFIG,
  ui: UI_CONFIG,
  monitoring: MONITORING_CONFIG,
  security: SECURITY_CONFIG,
  features: FEATURE_FLAGS,
  environment: ENV_CONFIG,
  cache: CACHE_CONFIG,
  performance: PERFORMANCE_CONFIG,
  error: ERROR_CONFIG,
};

export default CONFIG;
