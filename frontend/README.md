# 🛡️ Cyber Sentinel ML - Frontend

Enterprise-grade React dashboard for network threat detection and analysis.

## 📋 Overview

This is a modern, production-ready React application built with TypeScript, Ant Design, and enterprise-grade architecture patterns. It provides real-time threat monitoring, analytics, and configuration management for the Cyber Sentinel ML platform.

## 🚀 Quick Start

### Prerequisites

- **Node.js** 16.0.0 or higher
- **npm** 8.0.0 or higher
- **Git** for version control

### Setup Instructions

#### Windows (PowerShell)
```powershell
# Run the setup script
.\setup.ps1

# Or manually:
npm install
npm start
```

#### Linux/macOS (Bash)
```bash
# Make script executable and run
chmod +x setup.sh
./setup.sh

# Or manually:
npm install
npm start
```

#### Manual Setup
```bash
# Install dependencies
npm install

# Start development server
npm start

# Build for production
npm run build
```

## 🌐 Access Points

- **Development Server**: http://localhost:3000
- **API Gateway**: http://localhost:8000 (proxied)
- **Health Check**: http://localhost:3000/health

## 🏗️ Architecture

### Technology Stack

- **React 18** - Modern React with hooks and concurrent features
- **TypeScript** - Type-safe JavaScript development
- **Ant Design 5** - Enterprise UI component library
- **React Router 6** - Client-side routing
- **React Query** - Server state management and caching
- **Zustand** - Client state management
- **Socket.IO** - Real-time WebSocket connections
- **Axios** - HTTP client with interceptors
- **Framer Motion** - Animation library
- **Recharts** - Data visualization
- **React Hot Toast** - Notification system

### Project Structure

```
frontend/
├── 📁 public/              # Static assets
│   ├── index.html         # HTML template
│   ├── manifest.json      # PWA configuration
│   └── robots.txt         # SEO configuration
├── 📁 src/
│   ├── 📁 components/     # Reusable components
│   │   ├── Layout/        # Main layout component
│   │   └── Common/        # Shared components
│   ├── 📁 pages/          # Page components
│   │   ├── Dashboard/     # Main dashboard
│   │   ├── ThreatDetection/ # Threat monitoring
│   │   ├── AttackCategories/ # Attack rule management
│   │   ├── Analytics/     # Data analytics
│   │   ├── History/       # Threat history
│   │   └── Settings/      # Configuration
│   ├── 📁 services/       # API services
│   ├── 📁 store/          # State management
│   ├── 📁 config/         # Configuration constants
│   ├── App.tsx            # Main application component
│   ├── index.tsx          # Application entry point
│   └── styles/            # CSS and styling
├── 📄 package.json        # Dependencies and scripts
├── 📄 tsconfig.json       # TypeScript configuration
├── 📄 Dockerfile          # Container configuration
└── 📄 nginx.conf          # Production web server
```

## 🔧 Development

### Available Scripts

```bash
# Development
npm start              # Start development server
npm test               # Run tests in watch mode
npm run build          # Build for production

# Code Quality
npm run lint           # Check for linting errors
npm run lint:fix       # Fix linting errors automatically
npm run type-check     # Verify TypeScript types
npm run format         # Format code with Prettier

# Analysis
npm run analyze        # Analyze bundle size
npm run eject          # Eject from Create React App (irreversible)
```

### Environment Variables

Create a `.env` file in the root directory:

```env
# API Configuration
REACT_APP_API_URL=http://localhost:8000
REACT_APP_SOCKET_URL=http://localhost:8000

# Feature Flags
REACT_APP_FEATURE_REAL_TIME=true
REACT_APP_FEATURE_ANALYTICS=true
REACT_APP_FEATURE_ML_V2=true

# Environment
REACT_APP_ENVIRONMENT=development

# Analytics
REACT_APP_ERROR_REPORTING=false
REACT_APP_ANALYZE_BUNDLE=false

# Cache
REACT_APP_CACHE_VERSION=2.0.0
```

## 🎨 UI Components

### Ant Design Integration

The application uses Ant Design components with enterprise theming:

- **Layout** - Sidebar navigation and header
- **Tables** - Data display with sorting and pagination
- **Charts** - Recharts integration for analytics
- **Forms** - Configuration and input forms
- **Notifications** - Toast notifications for user feedback

### Theme System

- **Light/Dark Mode** - Toggle between themes
- **Enterprise Colors** - Professional color palette
- **Responsive Design** - Mobile-first approach
- **Accessibility** - WCAG 2.1 compliance

## 📊 Features

### Real-time Monitoring
- Live threat detection updates
- WebSocket-based notifications
- Real-time system metrics
- Performance monitoring

### Analytics & Reporting
- Interactive charts and graphs
- Export functionality (PDF, CSV, Excel)
- Custom date range filtering
- Performance benchmarks

### Configuration Management
- Attack category management
- System settings
- ML model configuration
- Security policies

### User Experience
- Role-based access control
- Responsive design
- Error boundaries
- Loading states
- Internationalization ready

## 🔒 Security

### Implementation
- **Authentication** - JWT token management
- **Authorization** - Role-based access control
- **CSRF Protection** - Anti-CSRF tokens
- **XSS Prevention** - Input sanitization
- **Secure Headers** - Content Security Policy

### Best Practices
- No sensitive data in client-side code
- Secure API communication
- Input validation
- Error handling without information disclosure

## 🚀 Deployment

### Docker Deployment

```bash
# Build Docker image
docker build -t cyber-sentinel-frontend .

# Run container
docker run -p 3000:3000 cyber-sentinel-frontend
```

### Production Build

```bash
# Build optimized production bundle
npm run build

# Serve with nginx (production)
docker build -f Dockerfile -t cyber-sentinel-frontend:prod .
```

### Kubernetes Deployment

```yaml
# Apply to Kubernetes cluster
kubectl apply -f k8s/frontend-deployment.yaml
kubectl apply -f k8s/frontend-service.yaml
```

## 🧪 Testing

### Test Structure

```
src/
├── __tests__/          # Test files
├── components/         # Component tests
├── pages/             # Page integration tests
├── services/          # API service tests
└── utils/             # Utility function tests
```

### Running Tests

```bash
# Run all tests
npm test

# Run tests with coverage
npm test -- --coverage

# Run tests in watch mode
npm test -- --watch

# Run specific test file
npm test -- Dashboard.test.tsx
```

### Testing Libraries

- **Jest** - Test runner and assertion library
- **React Testing Library** - Component testing utilities
- **MSW** - API mocking for tests
- **Cypress** - End-to-end testing (optional)

## 📈 Performance

### Optimization Features

- **Code Splitting** - Lazy loading of components
- **Bundle Analysis** - Size optimization tools
- **Image Optimization** - Responsive images
- **Caching** - Service worker and browser caching
- **Tree Shaking** - Dead code elimination

### Performance Metrics

- **First Contentful Paint**: < 1.5s
- **Largest Contentful Paint**: < 2.5s
- **Time to Interactive**: < 3.5s
- **Bundle Size**: < 2MB (gzipped)

## 🔍 Debugging

### Development Tools

- **React Developer Tools** - Component inspection
- **Redux DevTools** - State debugging (if using Redux)
- **Network Tab** - API request monitoring
- **Console Logging** - Structured logging

### Common Issues

1. **Module Not Found Errors**
   ```bash
   # Reinstall dependencies
   rm -rf node_modules package-lock.json
   npm install
   ```

2. **TypeScript Errors**
   ```bash
   # Check TypeScript configuration
   npm run type-check
   
   # Fix automatically
   npm run lint:fix
   ```

3. **Build Failures**
   ```bash
   # Clear cache and rebuild
   npm run build -- --reset-cache
   ```

## 📞 Support

### Getting Help

- **Documentation**: Check this README and inline code comments
- **Issues**: Report bugs via GitHub Issues
- **Community**: Join our Slack channel
- **Email**: frontend@cybersentinel.ai

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

### Code Standards

- **ESLint** - Code linting and formatting
- **Prettier** - Code formatting
- **TypeScript** - Type checking
- **Husky** - Git hooks for pre-commit checks

## 📄 License

MIT License - see LICENSE file for details.

## 🔗 Related Projects

- **Backend API**: Cyber Sentinel ML Python Services
- **Infrastructure**: Kubernetes and Terraform configurations
- **Documentation**: Full platform documentation
- **Monitoring**: Prometheus and Grafana dashboards

---

**Built with ❤️ by the Cyber Sentinel ML Team**

For enterprise support and custom implementations, contact enterprise@cybersentinel.ai
