import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Button, Typography } from 'antd';
import { ReloadOutlined } from '@ant-design/icons';

const { Title, Paragraph } = Typography;

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
  errorInfo?: ErrorInfo;
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.setState({
      error,
      errorInfo,
    });

    // Log error to monitoring service
    console.error('ErrorBoundary caught an error:', error, errorInfo);
  }

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-container">
          <Title level={2}>🚨 Something went wrong</Title>
          <Paragraph>
            The Cyber Sentinel application encountered an unexpected error.
            Our team has been notified and is working to fix this issue.
          </Paragraph>
          
          {process.env.NODE_ENV === 'development' && this.state.error && (
            <div style={{ textAlign: 'left', maxWidth: 600, margin: '20px auto' }}>
              <Paragraph>
                <strong>Error Details:</strong>
              </Paragraph>
              <pre style={{ 
                background: '#f5f5f5', 
                padding: '16px', 
                borderRadius: '4px',
                fontSize: '12px',
                overflow: 'auto'
              }}>
                {this.state.error.toString()}
                {this.state.errorInfo?.componentStack}
              </pre>
            </div>
          )}
          
          <Button 
            type="primary" 
            icon={<ReloadOutlined />}
            onClick={this.handleReload}
            size="large"
          >
            Reload Application
          </Button>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
