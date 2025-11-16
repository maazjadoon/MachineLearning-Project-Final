import React, { useState, useEffect } from 'react';
import { Card, Button, Table, Tag, Space, Typography, Alert, Input, Form } from 'antd';
import { PlayCircleOutlined, PauseCircleOutlined, ReloadOutlined } from '@ant-design/icons';
import { useAppStore } from '@/store/appStore';
import { api } from '@/services/api';

const { Title } = Typography;
const { TextArea } = Input;

const ThreatDetection: React.FC = () => {
  const { addNotification } = useAppStore();
  const [loading, setLoading] = useState(false);
  const [isDetecting, setIsDetecting] = useState(false);
  const [detections, setDetections] = useState<any[]>([]);
  const [testPacket, setTestPacket] = useState(`{
  "srcip": "192.168.1.100",
  "dstip": "10.0.0.50",
  "src_port": 12345,
  "dst_port": 22,
  "protocol": "TCP",
  "packet_size": 64,
  "flags": 18
}`);

  useEffect(() => {
    loadRecentDetections();
  }, []);

  const loadRecentDetections = async () => {
    try {
      setLoading(true);
      const response = await api.getThreatHistory({ limit: 50 });
      setDetections(response.data.detections || []);
    } catch (error) {
      console.error('Failed to load detections:', error);
      addNotification({
        type: 'error',
        message: 'Failed to load threat detections',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleTestDetection = async () => {
    try {
      setLoading(true);
      let packetData;
      
      try {
        packetData = JSON.parse(testPacket);
      } catch (e) {
        addNotification({
          type: 'error',
          message: 'Invalid JSON format for packet data',
        });
        return;
      }

      const response = await api.detectThreat(packetData);
      
      if (response.data.threat_detected) {
        addNotification({
          type: 'warning',
          message: `Threat detected: ${response.data.attack_type}`,
        });
      } else {
        addNotification({
          type: 'success',
          message: 'No threat detected',
        });
      }

      // Reload detections
      loadRecentDetections();
      
    } catch (error) {
      console.error('Detection test failed:', error);
      addNotification({
        type: 'error',
        message: 'Detection test failed',
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

  const columns = [
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
      render: (type: string) => type || 'Normal',
    },
    {
      title: 'Source IP',
      dataIndex: 'source_ip',
      key: 'source_ip',
    },
    {
      title: 'Destination IP',
      dataIndex: 'destination_ip',
      key: 'destination_ip',
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
    {
      title: 'Method',
      dataIndex: 'detection_method',
      key: 'detection_method',
      render: (method: string) => (
        <Tag color={method === 'ml_models' ? 'blue' : 'purple'}>
          {method === 'ml_models' ? 'ML' : 'Rules'}
        </Tag>
      ),
    },
  ];

  return (
    <div>
      <Title level={2}>Threat Detection</Title>
      
      {/* Detection Control */}
      <Card title="Detection Control" style={{ marginBottom: 24 }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <Alert
            message="Real-time Threat Detection"
            description={isDetecting ? "Threat detection is active and monitoring network traffic." : "Threat detection is paused."}
            type={isDetecting ? "success" : "warning"}
            showIcon
          />
          
          <Space>
            <Button
              type={isDetecting ? "default" : "primary"}
              icon={isDetecting ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
              onClick={() => setIsDetecting(!isDetecting)}
            >
              {isDetecting ? 'Pause Detection' : 'Start Detection'}
            </Button>
            
            <Button
              icon={<ReloadOutlined />}
              onClick={loadRecentDetections}
              loading={loading}
            >
              Refresh
            </Button>
          </Space>
        </Space>
      </Card>

      {/* Test Detection */}
      <Card title="Test Detection" style={{ marginBottom: 24 }}>
        <Form layout="vertical">
          <Form.Item label="Test Packet Data (JSON)">
            <TextArea
              value={testPacket}
              onChange={(e) => setTestPacket(e.target.value)}
              rows={8}
              placeholder="Enter packet data in JSON format"
            />
          </Form.Item>
          
          <Form.Item>
            <Button
              type="primary"
              onClick={handleTestDetection}
              loading={loading}
            >
              Test Detection
            </Button>
          </Form.Item>
        </Form>
      </Card>

      {/* Recent Detections */}
      <Card title="Recent Detections">
        <Table
          columns={columns}
          dataSource={detections}
          rowKey="packet_id"
          loading={loading}
          pagination={{
            pageSize: 20,
            showSizeChanger: true,
            showQuickJumper: true,
          }}
        />
      </Card>
    </div>
  );
};

export default ThreatDetection;
