import React, { useState, useEffect } from 'react';
import { Card, Table, Switch, Button, Tag, Space, Typography, Modal, Descriptions } from 'antd';
import { EyeOutlined, ReloadOutlined } from '@ant-design/icons';
import { useAppStore } from '@/store/appStore';
import { api } from '@/services/api';

const { Title } = Typography;

interface AttackCategory {
  id: string;
  name: string;
  category: string;
  severity: string;
  enabled: boolean;
  description: string;
  detection_rules: string[];
  auto_response: string;
}

const AttackCategories: React.FC = () => {
  const { addNotification } = useAppStore();
  const [loading, setLoading] = useState(false);
  const [categories, setCategories] = useState<AttackCategory[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<AttackCategory | null>(null);
  const [detailModalVisible, setDetailModalVisible] = useState(false);

  useEffect(() => {
    loadAttackCategories();
  }, []);

  const loadAttackCategories = async () => {
    try {
      setLoading(true);
      const response = await api.getAttackCategories();
      setCategories(response.data.categories || []);
    } catch (error) {
      console.error('Failed to load attack categories:', error);
      addNotification({
        type: 'error',
        message: 'Failed to load attack categories',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleToggleCategory = async (categoryId: string, enabled: boolean) => {
    try {
      if (enabled) {
        await api.enableAttackCategory(categoryId);
        addNotification({
          type: 'success',
          message: 'Attack category enabled',
        });
      } else {
        await api.disableAttackCategory(categoryId);
        addNotification({
          type: 'success',
          message: 'Attack category disabled',
        });
      }
      
      // Reload categories
      loadAttackCategories();
    } catch (error) {
      console.error('Failed to toggle category:', error);
      addNotification({
        type: 'error',
        message: 'Failed to update attack category',
      });
    }
  };

  const handleViewDetails = async (categoryId: string) => {
    try {
      const response = await api.getAttackCategoryInfo(categoryId);
      setSelectedCategory(response.data);
      setDetailModalVisible(true);
    } catch (error) {
      console.error('Failed to load category details:', error);
      addNotification({
        type: 'error',
        message: 'Failed to load category details',
      });
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

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'Network Attacks': return 'blue';
      case 'Malware': return 'purple';
      case 'Web Attacks': return 'orange';
      case 'Reconnaissance': return 'cyan';
      case 'Data Exfiltration': return 'red';
      default: return 'default';
    }
  };

  const columns = [
    {
      title: 'Attack Name',
      dataIndex: 'name',
      key: 'name',
      render: (name: string, record: AttackCategory) => (
        <div>
          <div style={{ fontWeight: 'bold' }}>{name}</div>
          <div style={{ fontSize: '12px', color: '#666' }}>{record.category}</div>
        </div>
      ),
    },
    {
      title: 'Category',
      dataIndex: 'category',
      key: 'category',
      render: (category: string) => (
        <Tag color={getCategoryColor(category)}>{category}</Tag>
      ),
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
      title: 'Detection Rules',
      dataIndex: 'detection_rules',
      key: 'detection_rules',
      render: (rules: string[]) => rules.length,
    },
    {
      title: 'Auto Response',
      dataIndex: 'auto_response',
      key: 'auto_response',
      render: (response: string) => (
        <Tag color={response === 'block_immediately' ? 'red' : 'orange'}>
          {response.replace('_', ' ').toUpperCase()}
        </Tag>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'enabled',
      key: 'enabled',
      render: (enabled: boolean, record: AttackCategory) => (
        <Switch
          checked={enabled}
          onChange={(checked) => handleToggleCategory(record.id, checked)}
          checkedChildren="ON"
          unCheckedChildren="OFF"
        />
      ),
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, record: AttackCategory) => (
        <Space>
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => handleViewDetails(record.id)}
          >
            Details
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Title level={2}>Attack Categories</Title>
      
      <Card
        title="Attack Detection Categories"
        extra={
          <Button
            icon={<ReloadOutlined />}
            onClick={loadAttackCategories}
            loading={loading}
          >
            Refresh
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={categories}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 20,
            showSizeChanger: true,
            showQuickJumper: true,
          }}
        />
      </Card>

      {/* Category Details Modal */}
      <Modal
        title={selectedCategory?.name}
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={null}
        width={800}
      >
        {selectedCategory && (
          <Descriptions column={2} bordered>
            <Descriptions.Item label="Category" span={2}>
              <Tag color={getCategoryColor(selectedCategory.category)}>
                {selectedCategory.category}
              </Tag>
            </Descriptions.Item>
            
            <Descriptions.Item label="Severity">
              <Tag color={getSeverityColor(selectedCategory.severity)}>
                {selectedCategory.severity}
              </Tag>
            </Descriptions.Item>
            
            <Descriptions.Item label="Status">
              <Tag color={selectedCategory.enabled ? 'green' : 'red'}>
                {selectedCategory.enabled ? 'Enabled' : 'Disabled'}
              </Tag>
            </Descriptions.Item>
            
            <Descriptions.Item label="Auto Response" span={2}>
              <Tag color={selectedCategory.auto_response === 'block_immediately' ? 'red' : 'orange'}>
                {selectedCategory.auto_response.replace('_', ' ').toUpperCase()}
              </Tag>
            </Descriptions.Item>
            
            <Descriptions.Item label="Description" span={2}>
              {selectedCategory.description}
            </Descriptions.Item>
            
            <Descriptions.Item label="Detection Rules" span={2}>
              <div style={{ maxHeight: '200px', overflowY: 'auto' }}>
                {selectedCategory.detection_rules.map((rule, index) => (
                  <div key={index} style={{ marginBottom: '8px' }}>
                    <Tag color="blue">{index + 1}</Tag> {rule}
                  </div>
                ))}
              </div>
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>
    </div>
  );
};

export default AttackCategories;
