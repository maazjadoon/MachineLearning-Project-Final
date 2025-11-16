import axios, { AxiosInstance } from 'axios';

// API configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Create axios instance
export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Add authentication token if available
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Add request timestamp
    (config as any).metadata = { startTime: new Date().getTime() };
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => {
    // Calculate request duration
    const endTime = new Date().getTime();
    const duration = endTime - (response.config as any).metadata?.startTime;
    
    // Log performance metrics in development
    if (process.env.NODE_ENV === 'development') {
      console.log(`API Request to ${response.config.url} took ${duration}ms`);
    }

    return response;
  },
  (error) => {
    // Handle common errors
    if (error.response?.status === 401) {
      // Unauthorized - redirect to login
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    } else if (error.response?.status === 429) {
      // Rate limited
      console.warn('Rate limit exceeded. Please try again later.');
    }

    return Promise.reject(error);
  }
);

// API endpoints
export const api = {
  // Health and status
  health: () => apiClient.get('/health'),
  status: () => apiClient.get('/status'),

  // Threat detection
  detectThreat: (packetData: any) => apiClient.post('/api/v1/threat/detect', packetData),
  batchDetectThreats: (packetsData: any) => apiClient.post('/api/v1/threat/batch-detect', packetsData),
  getThreatStats: () => apiClient.get('/api/v1/threat/stats'),
  getThreatHistory: (params?: any) => apiClient.get('/api/v1/threat/history', { params }),

  // ML models
  classifyPacket: (packetData: any) => apiClient.post('/api/v1/ml/classify', packetData),
  batchClassifyPackets: (packetsData: any) => apiClient.post('/api/v1/ml/batch-classify', packetsData),
  listModels: () => apiClient.get('/api/v1/ml/models'),
  getModelInfo: (modelName: string) => apiClient.get(`/api/v1/ml/models/${modelName}`),
  reloadModel: (modelName: string) => apiClient.post(`/api/v1/ml/models/${modelName}/reload`),

  // Analytics
  getAnalytics: (params?: any) => apiClient.get('/api/v1/analytics', { params }),
  getReports: (params?: any) => apiClient.get('/api/v1/analytics/reports', { params }),
  generateReport: (reportConfig: any) => apiClient.post('/api/v1/analytics/reports', reportConfig),

  // Configuration
  getConfig: () => apiClient.get('/api/v1/config'),
  updateConfig: (config: any) => apiClient.put('/api/v1/config', config),
  getAttackRules: () => apiClient.get('/api/v1/config/attack-rules'),
  updateAttackRules: (rules: any) => apiClient.put('/api/v1/config/attack-rules', rules),

  // Attack categories
  getAttackCategories: () => apiClient.get('/api/v1/threat/categories'),
  enableAttackCategory: (categoryId: string) => apiClient.post(`/api/v1/threat/categories/${categoryId}/enable`),
  disableAttackCategory: (categoryId: string) => apiClient.post(`/api/v1/threat/categories/${categoryId}/disable`),
  getAttackCategoryInfo: (categoryId: string) => apiClient.get(`/api/v1/threat/categories/${categoryId}`),
};

// Types for API responses
export interface ApiResponse<T = any> {
  success: boolean;
  data: T;
  message?: string;
  error?: string;
}

export interface ThreatDetectionResult {
  threat_detected: boolean;
  attack_type?: string;
  confidence: number;
  severity: string;
  timestamp: string;
  source_ip: string;
  destination_ip: string;
}

export interface SystemHealth {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  version: string;
  services: {
    [key: string]: string;
  };
}

export interface ThreatStats {
  timestamp: string;
  total_detections: number;
  threats_detected: number;
  attack_types: { [key: string]: number };
  severity_distribution: {
    CRITICAL: number;
    HIGH: number;
    MEDIUM: number;
    LOW: number;
  };
}

// Error handling utility
export const handleApiError = (error: any): string => {
  if (error.response?.data?.message) {
    return error.response.data.message;
  } else if (error.response?.data?.error) {
    return error.response.data.error;
  } else if (error.message) {
    return error.message;
  } else {
    return 'An unexpected error occurred';
  }
};

// Request wrapper with error handling
export const makeRequest = async <T>(
  requestFn: () => Promise<{ data: T }>
): Promise<T> => {
  try {
    const response = await requestFn();
    return response.data;
  } catch (error: any) {
    const errorMessage = handleApiError(error);
    throw new Error(errorMessage);
  }
};

export default apiClient;
