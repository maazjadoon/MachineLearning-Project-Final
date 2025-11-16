import { create } from 'zustand';
import { Socket } from 'socket.io-client';

export interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  message: string;
  duration?: number;
  timestamp: Date;
}

export interface SystemStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  version: string;
  services: {
    [key: string]: string;
  };
}

export interface RealTimeData {
  threats_detected: number;
  total_packets: number;
  accuracy: number;
  latency: number;
  timestamp: string;
}

export interface User {
  id: string;
  name: string;
  email: string;
  role: string;
}

interface AppState {
  // Theme
  theme: 'light' | 'dark';
  setTheme: (theme: 'light' | 'dark') => void;

  // Socket connection
  socket: Socket | null;
  setSocket: (socket: Socket | null) => void;

  // Notifications
  notifications: Notification[];
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp'>) => void;
  removeNotification: (id: string) => void;
  clearNotifications: () => void;

  // System status
  systemStatus: SystemStatus | null;
  updateSystemStatus: (status: SystemStatus) => void;

  // Real-time data
  realTimeData: RealTimeData | null;
  updateRealTimeData: (data: RealTimeData) => void;

  // User
  user: User | null;
  setUser: (user: User | null) => void;
  logout: () => void;

  // Loading states
  loading: boolean;
  setLoading: (loading: boolean) => void;

  // Error states
  error: string | null;
  setError: (error: string | null) => void;
}

export const useAppStore = create<AppState>((set, get) => ({
  // Theme
  theme: 'light',
  setTheme: (theme) => set({ theme }),

  // Socket connection
  socket: null,
  setSocket: (socket) => set({ socket }),

  // Notifications
  notifications: [],
  addNotification: (notification) => {
    const id = Date.now().toString();
    const newNotification: Notification = {
      ...notification,
      id,
      timestamp: new Date(),
    };
    
    set((state) => ({
      notifications: [...state.notifications, newNotification],
    }));

    // Auto-remove notification after duration
    if (notification.duration !== 0) {
      setTimeout(() => {
        get().removeNotification(id);
      }, notification.duration || 4000);
    }
  },
  removeNotification: (id) =>
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
    })),
  clearNotifications: () => set({ notifications: [] }),

  // System status
  systemStatus: null,
  updateSystemStatus: (systemStatus) => set({ systemStatus }),

  // Real-time data
  realTimeData: null,
  updateRealTimeData: (realTimeData) => set({ realTimeData }),

  // User
  user: {
    id: '1',
    name: 'Security Analyst',
    email: 'analyst@cybersentinel.ai',
    role: 'admin',
  },
  setUser: (user) => set({ user }),
  logout: () => set({ 
    user: null,
    notifications: [],
    error: null,
  }),

  // Loading states
  loading: false,
  setLoading: (loading) => set({ loading }),

  // Error states
  error: null,
  setError: (error) => set({ error }),
}));
