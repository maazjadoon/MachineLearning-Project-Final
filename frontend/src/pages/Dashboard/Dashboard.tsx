import React, { useEffect, useState } from 'react';
import { Card, Row, Col, Statistic, Typography, Progress, Table, Tag } from 'antd';
import {
  SecurityScanOutlined,
  ExclamationCircleOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons';
import { useAppStore } from '@/store/appStore';
import { api } from '@/services/api';

const { Title } = Typography;

const Dashboard: React.FC = () => {
  const { systemStatus, realTimeData, addNotification } = useAppStore();
  const [stats, setStats] = useState<any>(null);
  const [recentThreats, setRecentThreats] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
    
    // Refresh data every 30 seconds
    const interval = setInterval(loadDashboardData, 30000);
    
    return () => clearInterval(interval);
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      
      // Load threat stats
      const statsResponse = await api.getThreatStats();
      setStats(statsResponse.data);
      
      // Load recent threats
      const historyResponse = await api.getThreatHistory({ limit: 10 });
      setRecentThreats(historyResponse.data.detections || []);
      
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
      addNotification({
        type: 'error',
        message: 'Failed to load dashboard data',
      });
    } finally {
      setLoading(false);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'CRITICAL': return 'red';
      case 'HIGH': return 'orange';
      case 'MEDIUM': return 'yellow';
      case 'LOW': return 'green';
      default: return 'default';
    }
  };

  const threatColumns = [
    {
      title: 'Time',
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: (timestamp: string) => new Date(timestamp).toLocaleString(),
    },
    {
      title: 'Attack Type',
      dataIndex: 'attack_type',
      key: 'attack_type',
    },
    {
      title: 'Source IP',
      dataIndex: 'source_ip',
      key: 'source_ip',
    },
    {
      title: 'Confidence',
      dataIndex: 'confidence',
      key: 'confidence',
      render: (confidence: number) => `${(confidence * 100).toFixed(1)}%`,
    },
    {
      title: 'Severity',
      dataIndex: 'severity',
      key: 'severity',
      render: (severity: string) => (
        <Tag color={getSeverityColor(severity)}>{severity}</Tag>
      ),
    },
  ];

  return (
    <div>
      <Title level={2}>Dashboard</Title>
      
      {/* System Status */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="System Status"
              value={systemStatus?.status || 'Unknown'}
              prefix={
                systemStatus?.status === 'healthy' ? (
                  <CheckCircleOutlined style={{ color: '#52c41a' }} />
                ) : (
                  <ExclamationCircleOutlined style={{ color: '#faad14' }} />
                )
              }
            />
          </Card>
        </Col>
        
        <Col span={6}>
          <Card>
            <Statistic
              title="Total Detections"
              value={stats?.total_detections || 0}
              prefix={<SecurityScanOutlined />}
            />
          </Card>
        </Col>
        
        <Col span={6}>
          <Card>
            <Statistic
              title="Threats Detected"
              value={stats?.threats_detected || 0}
              valueStyle={{ color: '#cf1322' }}
              prefix={<ExclamationCircleOutlined />}
            />
          </Card>
        </Col>
        
        <Col span={6}>
          <Card>
            <Statistic
              title="Detection Rate"
              value={stats?.total_detections ? ((stats.threats_detected / stats.total_detections) * 100).toFixed(1) : 0}
              suffix="%"
              prefix={<ClockCircleOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* Real-time Metrics */}
      {realTimeData && (
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col span={8}>
            <Card title="Detection Accuracy">
              <Progress
                type="circle"
                percent={Math.round(realTimeData.accuracy * 100)}
                format={(percent) => `${percent}%`}
              />
            </Card>
          </Col>
          
          <Col span={8}>
            <Card title="Processing Latency">
              <Statistic
                value={realTimeData.latency}
                suffix="ms"
                valueStyle={{ color: realTimeData.latency < 100 ? '#3f8600' : '#cf1322' }}
              />
            </Card>
          </Col>
          
          <Col span={8}>
            <Card title="Packets Processed">
              <Statistic
                value={realTimeData.total_packets}
                suffix="packets"
                formatter={(value) => value?.toLocaleString()}
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* Recent Threats */}
      <Card title="Recent Threats" loading={loading}>
        <Table
          columns={threatColumns}
          dataSource={recentThreats}
          rowKey="packet_id"
          pagination={false}
          size="small"
        />
      </Card>
    </div>
  );
};

export default Dashboard;
