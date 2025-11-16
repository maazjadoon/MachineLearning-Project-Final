import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import { ConfigProvider, theme } from 'antd';
import { HelmetProvider } from 'react-helmet-async';
import { motion } from 'framer-motion';
import { Toaster } from 'react-hot-toast';
import io, { Socket } from 'socket.io-client';

// Components
import Layout from './components/Layout/Layout';
import Dashboard from './pages/Dashboard/Dashboard';
import ThreatDetection from './pages/ThreatDetection/ThreatDetection';
import AttackCategories from './pages/AttackCategories/AttackCategories';
import Analytics from './pages/Analytics/Analytics';
import Settings from './pages/Settings/Settings';
import History from './pages/History/History';
import LoadingScreen from './components/Common/LoadingScreen';
import ErrorBoundary from './components/Common/ErrorBoundary';

// Store
import { useAppStore } from './store/appStore';

// Services
import { apiClient } from './services/api';
import { SOCKET_URL } from './config/constants';

// Styles
import 'antd/dist/reset.css';
import './App.css';

// Create React Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 3,
      retryDelay: (attemptIndex: number) => Math.min(1000 * 2 ** attemptIndex, 30000),
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      refetchOnWindowFocus: false,
      refetchOnReconnect: true,
    },
    mutations: {
      retry: 1,
    },
  },
});

const App: React.FC = () => {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [loading, setLoading] = useState(true);
  const { 
    theme: appTheme, 
    setSocket: setSocketConnection, 
    addNotification,
    updateSystemStatus,
    updateRealTimeData 
  } = useAppStore();

  useEffect(() => {
    // Initialize application
    const initializeApp = async () => {
      try {
        // Check API health
        const healthResponse = await apiClient.get('/health');
        updateSystemStatus(healthResponse.data);

        // Initialize WebSocket connection
        const newSocket = io(SOCKET_URL, {
          transports: ['websocket', 'polling'],
          timeout: 20000,
          forceNew: true,
        });

        newSocket.on('connect', () => {
          console.log('🔌 Connected to WebSocket server');
          setSocket(newSocket);
          setSocketConnection(newSocket);
          addNotification({
            type: 'success',
            message: 'Real-time connection established',
            duration: 3000,
          });
        });

        newSocket.on('disconnect', () => {
          console.log('🔌 Disconnected from WebSocket server');
          addNotification({
            type: 'warning',
            message: 'Real-time connection lost',
            duration: 5000,
          });
        });

        newSocket.on('threat_update', (data: any) => {
          updateRealTimeData(data);
          addNotification({
            type: 'warning',
            message: `New threat detected: ${data.attack_type}`,
            duration: 4000,
          });
        });

        newSocket.on('system_update', (data: any) => {
          updateSystemStatus(data);
        });

        newSocket.on('stats_update', (data: any) => {
          updateRealTimeData(data);
        });

        newSocket.on('error', (error: any) => {
          console.error('WebSocket error:', error);
          addNotification({
            type: 'error',
            message: 'Connection error occurred',
            duration: 5000,
          });
        });

        setLoading(false);

      } catch (error) {
        console.error('Failed to initialize app:', error);
        addNotification({
          type: 'error',
          message: 'Failed to initialize application',
          duration: 5000,
        });
        setLoading(false);
      }
    };

    initializeApp();

    // Cleanup
    return () => {
      if (socket) {
        socket.disconnect();
      }
    };
  }, []);

  // Ant Design theme configuration
  const antdTheme = {
    algorithm: appTheme === 'dark' ? theme.darkAlgorithm : theme.defaultAlgorithm,
    token: {
      colorPrimary: '#1890ff',
      colorSuccess: '#52c41a',
      colorWarning: '#faad14',
      colorError: '#ff4d4f',
      borderRadius: 8,
      wireframe: false,
    },
    components: {
      Layout: {
        headerBg: appTheme === 'dark' ? '#001529' : '#ffffff',
        siderBg: appTheme === 'dark' ? '#001529' : '#f6f6f6',
      },
      Menu: {
        darkItemBg: '#001529',
        darkSubMenuItemBg: '#000c17',
      },
    },
  };

  if (loading) {
    return <LoadingScreen />;
  }

  return (
    <ErrorBoundary>
      <HelmetProvider>
        <QueryClientProvider client={queryClient}>
          <ConfigProvider theme={antdTheme}>
            <Router>
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.5 }}
                className="app"
              >
                <Layout>
                  <Routes>
                    <Route path="/" element={<Navigate to="/dashboard" replace />} />
                    <Route path="/dashboard" element={<Dashboard />} />
                    <Route path="/threat-detection" element={<ThreatDetection />} />
                    <Route path="/attack-categories" element={<AttackCategories />} />
                    <Route path="/analytics" element={<Analytics />} />
                    <Route path="/history" element={<History />} />
                    <Route path="/settings" element={<Settings />} />
                    <Route path="*" element={<Navigate to="/dashboard" replace />} />
                  </Routes>
                </Layout>
              </motion.div>
            </Router>
            <Toaster
              position="top-right"
              toastOptions={{
                duration: 4000,
                style: {
                  background: appTheme === 'dark' ? '#1f1f1f' : '#ffffff',
                  color: appTheme === 'dark' ? '#ffffff' : '#000000',
                },
                success: {
                  iconTheme: {
                    primary: '#52c41a',
                    secondary: '#ffffff',
                  },
                },
                error: {
                  iconTheme: {
                    primary: '#ff4d4f',
                    secondary: '#ffffff',
                  },
                },
              }}
            />
          </ConfigProvider>
        </QueryClientProvider>
      </HelmetProvider>
    </ErrorBoundary>
  );
};

export default App;
