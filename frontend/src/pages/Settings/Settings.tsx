import React, { useState, useEffect } from 'react';
import { Card, Form, Switch, Input, Button, Select, Typography, Divider, Space, Alert, Tabs } from 'antd';
import { SaveOutlined, ReloadOutlined } from '@ant-design/icons';
import { useAppStore } from '@/store/appStore';
import { api } from '@/services/api';

const { Title, Paragraph } = Typography;
const { Option } = Select;
const { TabPane } = Tabs;

interface SystemSettings {
  real_time_detection: boolean;
  auto_response: boolean;
  notification_email: string;
  log_level: string;
  max_connections: number;
  timeout: number;
}

interface SecuritySettings {
  session_timeout: number;
  max_login_attempts: number;
  password_policy: boolean;
  two_factor_auth: boolean;
  ip_whitelist: string;
}

interface MLSettings {
  model_version: string;
  confidence_threshold: number;
  batch_size: number;
  gpu_acceleration: boolean;
  auto_retraining: boolean;
}

const Settings: React.FC = () => {
  const { addNotification } = useAppStore();
  const [loading, setLoading] = useState(false);
  const [systemSettings, setSystemSettings] = useState<SystemSettings>({
    real_time_detection: true,
    auto_response: false,
    notification_email: '',
    log_level: 'INFO',
    max_connections: 1000,
    timeout: 30,
  });
  const [securitySettings, setSecuritySettings] = useState<SecuritySettings>({
    session_timeout: 3600,
    max_login_attempts: 5,
    password_policy: true,
    two_factor_auth: false,
    ip_whitelist: '',
  });
  const [mlSettings, setMLSettings] = useState<MLSettings>({
    model_version: 'v2.0.0',
    confidence_threshold: 0.8,
    batch_size: 32,
    gpu_acceleration: true,
    auto_retraining: true,
  });

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      setLoading(true);
      const response = await api.getConfig();
      const config = response.data;
      
      if (config.system) {
        setSystemSettings(config.system);
      }
      if (config.security) {
        setSecuritySettings(config.security);
      }
      if (config.ml) {
        setMLSettings(config.ml);
      }
    } catch (error) {
      console.error('Failed to load settings:', error);
      addNotification({
        type: 'error',
        message: 'Failed to load settings',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSaveSettings = async (category: string, settings: any) => {
    try {
      setLoading(true);
      await api.updateConfig({
        [category]: settings,
      });
      
      addNotification({
        type: 'success',
        message: `${category} settings saved successfully`,
      });
    } catch (error) {
      console.error('Failed to save settings:', error);
      addNotification({
        type: 'error',
        message: 'Failed to save settings',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSystemSettingsChange = (key: keyof SystemSettings, value: any) => {
    setSystemSettings(prev => ({
      ...prev,
      [key]: value,
    }));
  };

  const handleSecuritySettingsChange = (key: keyof SecuritySettings, value: any) => {
    setSecuritySettings(prev => ({
      ...prev,
      [key]: value,
    }));
  };

  const handleMLSettingsChange = (key: keyof MLSettings, value: any) => {
    setMLSettings(prev => ({
      ...prev,
      [key]: value,
    }));
  };

  return (
    <div>
      <Title level={2}>Settings</Title>
      
      <Tabs defaultActiveKey="system">
        {/* System Settings */}
        <TabPane tab="System" key="system">
          <Card title="System Configuration">
            <Form layout="vertical">
              <Form.Item label="Real-time Detection">
                <Switch
                  checked={systemSettings.real_time_detection}
                  onChange={(checked) => handleSystemSettingsChange('real_time_detection', checked)}
                />
                <Paragraph type="secondary" style={{ marginTop: 8 }}>
                  Enable real-time threat detection and monitoring
                </Paragraph>
              </Form.Item>

              <Form.Item label="Automatic Response">
                <Switch
                  checked={systemSettings.auto_response}
                  onChange={(checked) => handleSystemSettingsChange('auto_response', checked)}
                />
                <Paragraph type="secondary" style={{ marginTop: 8 }}>
                  Automatically block detected threats without manual intervention
                </Paragraph>
              </Form.Item>

              <Form.Item label="Notification Email">
                <Input
                  value={systemSettings.notification_email}
                  onChange={(e) => handleSystemSettingsChange('notification_email', e.target.value)}
                  placeholder="admin@cybersentinel.ai"
                />
                <Paragraph type="secondary" style={{ marginTop: 8 }}>
                  Email address for critical threat notifications
                </Paragraph>
              </Form.Item>

              <Form.Item label="Log Level">
                <Select
                  value={systemSettings.log_level}
                  onChange={(value) => handleSystemSettingsChange('log_level', value)}
                >
                  <Option value="DEBUG">Debug</Option>
                  <Option value="INFO">Info</Option>
                  <Option value="WARNING">Warning</Option>
                  <Option value="ERROR">Error</Option>
                  <Option value="CRITICAL">Critical</Option>
                </Select>
                <Paragraph type="secondary" style={{ marginTop: 8 }}>
                  Minimum level of logs to record
                </Paragraph>
              </Form.Item>

              <Form.Item label="Max Connections">
                <Input
                  type="number"
                  value={systemSettings.max_connections}
                  onChange={(e) => handleSystemSettingsChange('max_connections', parseInt(e.target.value))}
                />
                <Paragraph type="secondary" style={{ marginTop: 8 }}>
                  Maximum number of concurrent connections
                </Paragraph>
              </Form.Item>

              <Form.Item label="Request Timeout (seconds)">
                <Input
                  type="number"
                  value={systemSettings.timeout}
                  onChange={(e) => handleSystemSettingsChange('timeout', parseInt(e.target.value))}
                />
                <Paragraph type="secondary" style={{ marginTop: 8 }}>
                  Request timeout in seconds
                </Paragraph>
              </Form.Item>

              <Divider />

              <Space>
                <Button
                  type="primary"
                  icon={<SaveOutlined />}
                  onClick={() => handleSaveSettings('system', systemSettings)}
                  loading={loading}
                >
                  Save System Settings
                </Button>
                <Button
                  icon={<ReloadOutlined />}
                  onClick={loadSettings}
                  loading={loading}
                >
                  Reset
                </Button>
              </Space>
            </Form>
          </Card>
        </TabPane>

        {/* Security Settings */}
        <TabPane tab="Security" key="security">
          <Card title="Security Configuration">
            <Form layout="vertical">
              <Form.Item label="Session Timeout (seconds)">
                <Input
                  type="number"
                  value={securitySettings.session_timeout}
                  onChange={(e) => handleSecuritySettingsChange('session_timeout', parseInt(e.target.value))}
                />
                <Paragraph type="secondary" style={{ marginTop: 8 }}>
                  User session timeout in seconds
                </Paragraph>
              </Form.Item>

              <Form.Item label="Max Login Attempts">
                <Input
                  type="number"
                  value={securitySettings.max_login_attempts}
                  onChange={(e) => handleSecuritySettingsChange('max_login_attempts', parseInt(e.target.value))}
                />
                <Paragraph type="secondary" style={{ marginTop: 8 }}>
                  Maximum failed login attempts before account lockout
                </Paragraph>
              </Form.Item>

              <Form.Item label="Password Policy">
                <Switch
                  checked={securitySettings.password_policy}
                  onChange={(checked) => handleSecuritySettingsChange('password_policy', checked)}
                />
                <Paragraph type="secondary" style={{ marginTop: 8 }}>
                  Enforce strong password requirements
                </Paragraph>
              </Form.Item>

              <Form.Item label="Two-Factor Authentication">
                <Switch
                  checked={securitySettings.two_factor_auth}
                  onChange={(checked) => handleSecuritySettingsChange('two_factor_auth', checked)}
                />
                <Paragraph type="secondary" style={{ marginTop: 8 }}>
                  Require two-factor authentication for all users
                </Paragraph>
              </Form.Item>

              <Form.Item label="IP Whitelist">
                <Input.TextArea
                  value={securitySettings.ip_whitelist}
                  onChange={(e) => handleSecuritySettingsChange('ip_whitelist', e.target.value)}
                  rows={4}
                  placeholder="192.168.1.0/24&#10;10.0.0.0/8"
                />
                <Paragraph type="secondary" style={{ marginTop: 8 }}>
                  Comma-separated list of allowed IP ranges (one per line)
                </Paragraph>
              </Form.Item>

              <Divider />

              <Space>
                <Button
                  type="primary"
                  icon={<SaveOutlined />}
                  onClick={() => handleSaveSettings('security', securitySettings)}
                  loading={loading}
                >
                  Save Security Settings
                </Button>
                <Button
                  icon={<ReloadOutlined />}
                  onClick={loadSettings}
                  loading={loading}
                >
                  Reset
                </Button>
              </Space>
            </Form>
          </Card>
        </TabPane>

        {/* ML Settings */}
        <TabPane tab="Machine Learning" key="ml">
          <Card title="ML Configuration">
            <Form layout="vertical">
              <Form.Item label="Model Version">
                <Select
                  value={mlSettings.model_version}
                  onChange={(value) => handleMLSettingsChange('model_version', value)}
                >
                  <Option value="v2.0.0">v2.0.0 (Latest)</Option>
                  <Option value="v1.9.0">v1.9.0</Option>
                  <Option value="v1.8.0">v1.8.0</Option>
                </Select>
                <Paragraph type="secondary" style={{ marginTop: 8 }}>
                  Active ML model version for threat detection
                </Paragraph>
              </Form.Item>

              <Form.Item label="Confidence Threshold">
                <Input
                  type="number"
                  step="0.1"
                  min="0"
                  max="1"
                  value={mlSettings.confidence_threshold}
                  onChange={(e) => handleMLSettingsChange('confidence_threshold', parseFloat(e.target.value))}
                />
                <Paragraph type="secondary" style={{ marginTop: 8 }}>
                  Minimum confidence level to consider a detection valid (0.0-1.0)
                </Paragraph>
              </Form.Item>

              <Form.Item label="Batch Size">
                <Input
                  type="number"
                  value={mlSettings.batch_size}
                  onChange={(e) => handleMLSettingsChange('batch_size', parseInt(e.target.value))}
                />
                <Paragraph type="secondary" style={{ marginTop: 8 }}>
                  Number of packets to process in each batch
                </Paragraph>
              </Form.Item>

              <Form.Item label="GPU Acceleration">
                <Switch
                  checked={mlSettings.gpu_acceleration}
                  onChange={(checked) => handleMLSettingsChange('gpu_acceleration', checked)}
                />
                <Paragraph type="secondary" style={{ marginTop: 8 }}>
                  Use GPU acceleration for ML inference (if available)
                </Paragraph>
              </Form.Item>

              <Form.Item label="Automatic Retraining">
                <Switch
                  checked={mlSettings.auto_retraining}
                  onChange={(checked) => handleMLSettingsChange('auto_retraining', checked)}
                />
                <Paragraph type="secondary" style={{ marginTop: 8 }}>
                  Automatically retrain models with new data
                </Paragraph>
              </Form.Item>

              <Alert
                message="Model Performance"
                description="Current model accuracy: 99.7% | Processing speed: 45ms | Last trained: 2024-01-15"
                type="info"
                showIcon
                style={{ marginBottom: 16 }}
              />

              <Divider />

              <Space>
                <Button
                  type="primary"
                  icon={<SaveOutlined />}
                  onClick={() => handleSaveSettings('ml', mlSettings)}
                  loading={loading}
                >
                  Save ML Settings
                </Button>
                <Button
                  icon={<ReloadOutlined />}
                  onClick={loadSettings}
                  loading={loading}
                >
                  Reset
                </Button>
              </Space>
            </Form>
          </Card>
        </TabPane>
      </Tabs>
    </div>
  );
};

export default Settings;
