import React from 'react';
import { Spin, Typography } from 'antd';
import { SecurityScanOutlined } from '@ant-design/icons';

const { Title } = Typography;

const LoadingScreen: React.FC = () => {
  return (
    <div className="loading-container">
      <div style={{ textAlign: 'center' }}>
        <SecurityScanOutlined style={{ fontSize: 64, color: '#1890ff', marginBottom: 24 }} />
        <Title level={3}>Cyber Sentinel ML</Title>
        <Spin size="large" />
        <div style={{ marginTop: 16, color: '#666' }}>
          Initializing enterprise threat detection system...
        </div>
      </div>
    </div>
  );
};

export default LoadingScreen;
