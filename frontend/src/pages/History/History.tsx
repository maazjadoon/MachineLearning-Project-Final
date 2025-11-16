import React, { useState, useEffect } from 'react';
import { Card, Table, Tag, DatePicker, Select, Button, Space, Typography, Input } from 'antd';
import { ReloadOutlined, DownloadOutlined } from '@ant-design/icons';
import { useAppStore } from '@/store/appStore';
import { api } from '@/services/api';

const { Title } = Typography;
const { RangePicker } = DatePicker;
const { Option } = Select;
const { Search } = Input;

interface HistoryRecord {
  id: string;
  timestamp: string;
  attack_type: string;
  source_ip: string;
  destination_ip: string;
  confidence: number;
  severity: string;
  detection_method: string;
  status: string;
}

const History: React.FC = () => {
  const { addNotification } = useAppStore();
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState<HistoryRecord[]>([]);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 20,
    total: 0,
  });
  const [filters, setFilters] = useState({
    dateRange: null as any,
    attackType: 'all',
    severity: 'all',
    search: '',
  });

  useEffect(() => {
    loadHistory();
  }, [pagination.current, pagination.pageSize, filters]);

  const loadHistory = async () => {
    try {
      setLoading(true);
      const response = await api.getThreatHistory({
        limit: pagination.pageSize,
        offset: (pagination.current - 1) * pagination.pageSize,
        start_date: filters.dateRange?.[0]?.toISOString(),
        end_date: filters.dateRange?.[1]?.toISOString(),
        attack_type: filters.attackType !== 'all' ? filters.attackType : undefined,
        severity: filters.severity !== 'all' ? filters.severity : undefined,
        search: filters.search || undefined,
      });
      
      setHistory(response.data.detections || []);
      setPagination(prev => ({
        ...prev,
        total: response.data.total_count || 0,
      }));
    } catch (error) {
      console.error('Failed to load history:', error);
      addNotification({
        type: 'error',
        message: 'Failed to load threat history',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleTableChange = (newPagination: any) => {
    setPagination(newPagination);
  };

  const handleFilterChange = (key: string, value: any) => {
    setFilters(prev => ({
      ...prev,
      [key]: value,
    }));
    setPagination(prev => ({
      ...prev,
      current: 1, // Reset to first page when filters change
    }));
  };

  const handleExport = async () => {
    try {
      setLoading(true);
      const response = await api.getThreatHistory({
        ...filters,
        limit: 10000, // Export all records
        format: 'csv',
      });
      
      // Create CSV download
      const csvContent = response.data;
      const blob = new Blob([csvContent], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `threat-history-${Date.now()}.csv`;
      a.click();
      window.URL.revokeObjectURL(url);
      
      addNotification({
        type: 'success',
        message: 'History exported successfully',
      });
    } catch (error) {
      console.error('Failed to export history:', error);
      addNotification({
        type: 'error',
        message: 'Failed to export history',
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

  const getMethodColor = (method: string) => {
    switch (method) {
      case 'ml_models': return 'blue';
      case 'automatic_rules': return 'purple';
      default: return 'default';
    }
  };

  const columns = [
    {
      title: 'Timestamp',
      dataIndex: 'timestamp',
      key: 'timestamp',
      width: 180,
      render: (timestamp: string) => new Date(timestamp).toLocaleString(),
      sorter: true,
    },
    {
      title: 'Attack Type',
      dataIndex: 'attack_type',
      key: 'attack_type',
      width: 150,
      render: (type: string) => type || 'Normal',
      sorter: true,
    },
    {
      title: 'Source IP',
      dataIndex: 'source_ip',
      key: 'source_ip',
      width: 140,
      sorter: true,
    },
    {
      title: 'Destination IP',
      dataIndex: 'destination_ip',
      key: 'destination_ip',
      width: 140,
      sorter: true,
    },
    {
      title: 'Confidence',
      dataIndex: 'confidence',
      key: 'confidence',
      width: 120,
      render: (confidence: number) => `${(confidence * 100).toFixed(1)}%`,
      sorter: true,
    },
    {
      title: 'Severity',
      dataIndex: 'severity',
      key: 'severity',
      width: 100,
      render: (severity: string) => (
        <Tag color={getSeverityColor(severity)}>{severity}</Tag>
      ),
      sorter: true,
    },
    {
      title: 'Method',
      dataIndex: 'detection_method',
      key: 'detection_method',
      width: 100,
      render: (method: string) => (
        <Tag color={getMethodColor(method)}>
          {method === 'ml_models' ? 'ML' : 'Rules'}
        </Tag>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => (
        <Tag color={status === 'resolved' ? 'green' : 'orange'}>
          {status || 'Active'}
        </Tag>
      ),
    },
  ];

  return (
    <div>
      <Title level={2}>Threat Detection History</Title>
      
      {/* Filters */}
      <Card style={{ marginBottom: 24 }}>
        <Space wrap>
          <Search
            placeholder="Search by IP, attack type..."
            style={{ width: 250 }}
            onSearch={(value) => handleFilterChange('search', value)}
            allowClear
          />
          
          <RangePicker
            showTime
            onChange={(dates) => handleFilterChange('dateRange', dates)}
            placeholder={['Start Date', 'End Date']}
          />
          
          <Select
            value={filters.attackType}
            style={{ width: 150 }}
            onChange={(value) => handleFilterChange('attackType', value)}
          >
            <Option value="all">All Attack Types</Option>
            <Option value="port_scan">Port Scan</Option>
            <Option value="ddos">DDoS</Option>
            <Option value="brute_force">Brute Force</Option>
            <Option value="sql_injection">SQL Injection</Option>
            <Option value="xss">XSS</Option>
          </Select>
          
          <Select
            value={filters.severity}
            style={{ width: 120 }}
            onChange={(value) => handleFilterChange('severity', value)}
          >
            <Option value="all">All Severities</Option>
            <Option value="critical">Critical</Option>
            <Option value="high">High</Option>
            <Option value="medium">Medium</Option>
            <Option value="low">Low</Option>
          </Select>
          
          <Button
            icon={<ReloadOutlined />}
            onClick={loadHistory}
            loading={loading}
          >
            Refresh
          </Button>
          
          <Button
            icon={<DownloadOutlined />}
            onClick={handleExport}
            loading={loading}
          >
            Export
          </Button>
        </Space>
      </Card>

      {/* History Table */}
      <Card title={`Detection History (${pagination.total} records)`}>
        <Table
          columns={columns}
          dataSource={history}
          rowKey="id"
          loading={loading}
          pagination={{
            ...pagination,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) =>
              `${range[0]}-${range[1]} of ${total} records`,
          }}
          onChange={handleTableChange}
          scroll={{ x: 1200 }}
        />
      </Card>
    </div>
  );
};

export default History;
