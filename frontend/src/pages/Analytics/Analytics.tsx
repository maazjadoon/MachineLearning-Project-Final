import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Typography, DatePicker, Select, Button, Space } from 'antd';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, PieChart, Pie, Cell, BarChart, Bar } from 'recharts';
import { ReloadOutlined, DownloadOutlined } from '@ant-design/icons';
import { useAppStore } from '@/store/appStore';
import { api } from '@/services/api';

const { Title } = Typography;
const { RangePicker } = DatePicker;
const { Option } = Select;

const Analytics: React.FC = () => {
  const { addNotification } = useAppStore();
  const [loading, setLoading] = useState(false);
  const [timeRange, setTimeRange] = useState<[any, any] | null>(null);

  useEffect(() => {
    loadAnalyticsData();
  }, []);

  const loadAnalyticsData = async () => {
    try {
      setLoading(true);
      const response = await api.getAnalytics({
        start_date: timeRange?.[0]?.toISOString(),
        end_date: timeRange?.[1]?.toISOString(),
      });
      console.log('Analytics data loaded:', response.data);
    } catch (error) {
      console.error('Failed to load analytics data:', error);
      addNotification({
        type: 'error',
        message: 'Failed to load analytics data',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleExportReport = async () => {
    try {
      setLoading(true);
      const response = await api.generateReport({
        time_range: timeRange,
        format: 'pdf',
      });
      
      // Download the report
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `cyber-sentinel-report-${Date.now()}.pdf`;
      a.click();
      window.URL.revokeObjectURL(url);
      
      addNotification({
        type: 'success',
        message: 'Report exported successfully',
      });
    } catch (error) {
      console.error('Failed to export report:', error);
      addNotification({
        type: 'error',
        message: 'Failed to export report',
      });
    } finally {
      setLoading(false);
    }
  };

  // Mock data for demonstration
  const mockTimeSeriesData = [
    { time: '00:00', threats: 12, packets: 1500 },
    { time: '04:00', threats: 8, packets: 1200 },
    { time: '08:00', threats: 25, packets: 2500 },
    { time: '12:00', threats: 18, packets: 2200 },
    { time: '16:00', threats: 32, packets: 3000 },
    { time: '20:00', threats: 15, packets: 1800 },
  ];

  const mockAttackTypeData = [
    { name: 'Port Scan', value: 45, color: '#1890ff' },
    { name: 'DDoS', value: 30, color: '#52c41a' },
    { name: 'Brute Force', value: 20, color: '#faad14' },
    { name: 'SQL Injection', value: 15, color: '#ff4d4f' },
    { name: 'XSS', value: 10, color: '#722ed1' },
  ];

  const mockSeverityData = [
    { severity: 'Critical', count: 5 },
    { severity: 'High', count: 15 },
    { severity: 'Medium', count: 35 },
    { severity: 'Low', count: 45 },
  ];

  return (
    <div>
      <Title level={2}>Analytics</Title>
      
      {/* Controls */}
      <Card style={{ marginBottom: 24 }}>
        <Space>
          <RangePicker
            showTime
            onChange={(dates) => setTimeRange(dates)}
            placeholder={['Start Date', 'End Date']}
          />
          
          <Select
            defaultValue="all"
            style={{ width: 120 }}
            placeholder="Attack Type"
          >
            <Option value="all">All Types</Option>
            <Option value="port_scan">Port Scan</Option>
            <Option value="ddos">DDoS</Option>
            <Option value="brute_force">Brute Force</Option>
          </Select>
          
          <Button
            icon={<ReloadOutlined />}
            onClick={loadAnalyticsData}
            loading={loading}
          >
            Refresh
          </Button>
          
          <Button
            icon={<DownloadOutlined />}
            onClick={handleExportReport}
            loading={loading}
          >
            Export Report
          </Button>
        </Space>
      </Card>

      {/* Charts */}
      <Row gutter={[16, 16]}>
        {/* Threat Trends */}
        <Col span={24}>
          <Card title="Threat Detection Trends" loading={loading}>
            <LineChart width={800} height={300} data={mockTimeSeriesData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis yAxisId="left" />
              <YAxis yAxisId="right" orientation="right" />
              <Tooltip />
              <Legend />
              <Line
                yAxisId="left"
                type="monotone"
                dataKey="threats"
                stroke="#ff4d4f"
                strokeWidth={2}
                name="Threats Detected"
              />
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="packets"
                stroke="#1890ff"
                strokeWidth={2}
                name="Packets Processed"
              />
            </LineChart>
          </Card>
        </Col>

        {/* Attack Types Distribution */}
        <Col span={12}>
          <Card title="Attack Types Distribution" loading={loading}>
            <PieChart width={400} height={300}>
              <Pie
                data={mockAttackTypeData}
                cx={200}
                cy={150}
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {mockAttackTypeData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </Card>
        </Col>

        {/* Severity Distribution */}
        <Col span={12}>
          <Card title="Severity Distribution" loading={loading}>
            <BarChart width={400} height={300} data={mockSeverityData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="severity" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="count" fill="#1890ff" />
            </BarChart>
          </Card>
        </Col>

        {/* Key Metrics */}
        <Col span={24}>
          <Card title="Key Metrics" loading={loading}>
            <Row gutter={[16, 16]}>
              <Col span={6}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#ff4d4f' }}>
                    156
                  </div>
                  <div style={{ color: '#666' }}>Total Threats</div>
                </div>
              </Col>
              <Col span={6}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#52c41a' }}>
                    98.5%
                  </div>
                  <div style={{ color: '#666' }}>Detection Accuracy</div>
                </div>
              </Col>
              <Col span={6}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#1890ff' }}>
                    45ms
                  </div>
                  <div style={{ color: '#666' }}>Avg Response Time</div>
                </div>
              </Col>
              <Col span={6}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#faad14' }}>
                    2.3M
                  </div>
                  <div style={{ color: '#666' }}>Packets Processed</div>
                </div>
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Analytics;
