import React, { ReactNode } from 'react';
import { Layout as AntLayout, Menu, Typography, Button, Dropdown, Space } from 'antd';
import {
  DashboardOutlined,
  SecurityScanOutlined,
  SettingOutlined,
  HistoryOutlined,
  BarChartOutlined,
  UserOutlined,
  BellOutlined,
  LogoutOutlined,
  SunOutlined,
  MoonOutlined
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAppStore } from '@/store/appStore';

const { Header, Sider, Content } = AntLayout;
const { Title } = Typography;

interface LayoutProps {
  children: ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { theme, setTheme, user, logout } = useAppStore();

  const menuItems = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: 'Dashboard',
    },
    {
      key: '/threat-detection',
      icon: <SecurityScanOutlined />,
      label: 'Threat Detection',
    },
    {
      key: '/attack-categories',
      icon: <BarChartOutlined />,
      label: 'Attack Categories',
    },
    {
      key: '/analytics',
      icon: <BarChartOutlined />,
      label: 'Analytics',
    },
    {
      key: '/history',
      icon: <HistoryOutlined />,
      label: 'History',
    },
    {
      key: '/settings',
      icon: <SettingOutlined />,
      label: 'Settings',
    },
  ];

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key);
  };

  const handleThemeToggle = () => {
    setTheme(theme === 'light' ? 'dark' : 'light');
  };

  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: 'Profile',
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: 'Settings',
    },
    {
      type: 'divider' as const,
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: 'Logout',
      onClick: logout,
    },
  ];

  return (
    <AntLayout className="enterprise-layout">
      <Sider
        theme={theme}
        width={250}
        style={{
          overflow: 'auto',
          height: '100vh',
          position: 'fixed',
          left: 0,
          top: 0,
          bottom: 0,
        }}
      >
        <div style={{ padding: '16px', textAlign: 'center' }}>
          <Title level={4} style={{ color: theme === 'dark' ? '#fff' : '#1890ff', margin: 0 }}>
            🛡️ Cyber Sentinel
          </Title>
        </div>
        <Menu
          theme={theme}
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={handleMenuClick}
        />
      </Sider>
      
      <AntLayout style={{ marginLeft: 250 }}>
        <Header
          style={{
            padding: '0 24px',
            background: theme === 'dark' ? '#1f1f1f' : '#fff',
            borderBottom: `1px solid ${theme === 'dark' ? '#303030' : '#f0f0f0'}`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <Title level={5} style={{ margin: 0, color: theme === 'dark' ? '#fff' : '#000' }}>
              Enterprise Threat Detection
            </Title>
          </div>
          
          <Space size="middle">
            <Button
              type="text"
              icon={theme === 'dark' ? <SunOutlined /> : <MoonOutlined />}
              onClick={handleThemeToggle}
            />
            
            <Button type="text" icon={<BellOutlined />} />
            
            <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
              <Button type="text" icon={<UserOutlined />}>
                {user?.name || 'User'}
              </Button>
            </Dropdown>
          </Space>
        </Header>
        
        <Content className="enterprise-main">
          {children}
        </Content>
      </AntLayout>
    </AntLayout>
  );
};

export default Layout;
