# 🚀 Cyber Sentinel ML - Enterprise Quick Start Guide

## 📋 Overview

This guide provides step-by-step instructions for deploying Cyber Sentinel ML in enterprise environments with production-grade infrastructure.

## 🎯 Prerequisites

### Required Tools
- **Docker** 20.10+
- **Kubernetes** 1.24+ (kubectl)
- **Terraform** 1.3+
- **AWS CLI** 2.0+ (for AWS deployment)
- **Helm** 3.8+ (optional)

### Infrastructure Requirements
- **Cloud Account**: AWS, GCP, or Azure
- **Domain**: Custom domain for SSL certificates
- **Resources**: Minimum 16 vCPU, 32GB RAM, 500GB storage

## 🏗️ Deployment Options

### Option 1: Docker Compose (Development)
**Best for**: Local development, testing, demonstrations

```bash
# Clone repository
git clone https://github.com/your-org/cyber-sentinel-ml.git
cd cyber-sentinel-ml

# Start all services
docker-compose -f docker-compose.enterprise.yml up -d

# Access services
open http://localhost:3000  # Frontend
open http://localhost:8000  # API Gateway
open http://localhost:9090  # Prometheus
open http://localhost:3001  # Grafana
```

### Option 2: Kubernetes (Production)
**Best for**: Production, staging, scalable deployments

```bash
# Deploy to Kubernetes
./scripts/deploy-enterprise.sh --environment production

# Check deployment
kubectl get pods -n cyber-sentinel
kubectl get services -n cyber-sentinel
```

### Option 3: Terraform + Kubernetes (Enterprise)
**Best for**: Full enterprise infrastructure with IaC

```bash
# Deploy infrastructure
cd terraform
terraform init
terraform plan -var="environment=production"
terraform apply -var="environment=production"

# Deploy applications
cd ..
./scripts/deploy-enterprise.sh --environment production
```

## 🔧 Step-by-Step Enterprise Deployment

### Step 1: Environment Setup

```bash
# Clone and setup
git clone https://github.com/your-org/cyber-sentinel-ml.git
cd cyber-sentinel-ml

# Configure environment
cp config/deployment.env.example config/deployment.env
# Edit config/deployment.env with your settings

# Install dependencies
pip install -r requirements.txt
cd frontend && npm install && cd ..
```

### Step 2: Infrastructure Deployment

```bash
# Deploy cloud infrastructure
./scripts/deploy-infrastructure.sh --environment production

# This creates:
# - VPC and networking
# - Kubernetes cluster (EKS/GKE/AKS)
# - Databases (PostgreSQL, Redis)
# - Storage (S3/MinIO)
# - Load balancers and security
# - Monitoring stack
```

### Step 3: Application Deployment

```bash
# Build and deploy all services
./scripts/deploy-enterprise.sh \
  --environment production \
  --tag v2.0.0 \
  --force

# This will:
# - Build Docker images for all microservices
# - Push to container registry
# - Deploy to Kubernetes with Helm charts
# - Configure monitoring and alerting
# - Run health checks and smoke tests
```

### Step 4: Verification

```bash
# Check deployment status
kubectl get pods -n cyber-sentinel
kubectl get services -n cyber-sentinel

# Run health checks
./scripts/health-check.sh --environment production

# Run smoke tests
./scripts/smoke-tests.sh --environment production

# Access dashboard
kubectl get ingress -n cyber-sentinel
# Open the provided URL in your browser
```

## 📊 Service Architecture

### Microservices
- **Threat Detection Service** (Port 5000) - Real-time threat analysis
- **ML Model Service** (Port 9999) - ML inference and model serving
- **Analytics Service** (Port 6000) - Data analytics and reporting
- **Configuration Service** (Port 7000) - Centralized config management
- **Web Frontend** (Port 3000) - React dashboard

### Infrastructure Components
- **API Gateway** - Authentication, rate limiting, routing
- **PostgreSQL** - Primary database (Port 5432)
- **Redis** - Caching and sessions (Port 6379)
- **Kafka** - Event streaming (Port 9092)
- **Elasticsearch** - Logging and search (Port 9200)
- **Prometheus** - Metrics collection (Port 9090)
- **Grafana** - Dashboards and visualization (Port 3000)
- **Jaeger** - Distributed tracing (Port 16686)

## 🔒 Security Configuration

### SSL/TLS Setup
```bash
# Install cert-manager
kubectl apply -f https://github.com/jetstack/cert-manager/releases/download/v1.8.0/cert-manager.yaml

# Configure SSL certificates
kubectl apply -f config/cert-manager/cluster-issuer.yaml
```

### Security Hardening
```bash
# Apply security policies
kubectl apply -f config/security/pod-security-policy.yaml
kubectl apply -f config/security/network-policy.yaml
kubectl apply -f config/security/rbac.yaml
```

### Authentication
```bash
# Configure OAuth2/OIDC
kubectl apply -f config/auth/oauth2.yaml

# Set up RBAC
kubectl apply -f config/auth/rbac.yaml
```

## 📈 Monitoring Setup

### Prometheus Configuration
```bash
# Import monitoring configuration
kubectl apply -f config/prometheus/

# Import Grafana dashboards
./scripts/import-grafana-dashboards.sh
```

### Alerting Rules
```bash
# Configure alerting
kubectl apply -f config/alertmanager/

# Test alerts
./scripts/test-alerts.sh
```

## 🧪 Testing Strategy

### Pre-deployment Tests
```bash
# Run all test suites
./scripts/run-tests.sh --environment production

# Individual tests
./scripts/unit-tests.sh
./scripts/integration-tests.sh
./scripts/load-tests.sh
./scripts/security-tests.sh
```

### Post-deployment Tests
```bash
# Health checks
curl -f https://api.cybersentinel.ai/health

# Functionality tests
curl -f https://api.cybersentinel.ai/api/v1/threat/stats

# Performance tests
k6 run tests/performance/production-load.js
```

## 🔄 CI/CD Pipeline

### GitHub Actions Setup
```bash
# Configure GitHub secrets
# - DOCKER_REGISTRY
# - KUBE_CONFIG
# - AWS_CREDENTIALS
# - SLACK_WEBHOOK

# Pipeline automatically:
# - Runs tests on every commit
# - Builds and pushes Docker images
# - Deploys to staging on develop branch
# - Deploys to production on release
# - Runs security scans and monitoring
```

### Manual Deployment
```bash
# Deploy specific version
./scripts/deploy-enterprise.sh --environment production --tag v2.1.0

# Blue-green deployment
./scripts/blue-green-deploy.sh --environment production

# Rollback deployment
./scripts/rollback.sh --environment production --to v2.0.0
```

## 📊 Performance Optimization

### Database Optimization
```sql
-- Create performance indexes
CREATE INDEX CONCURRENTLY idx_threat_detections_timestamp 
ON threat_detections(timestamp);

-- Partition large tables
CREATE TABLE threat_detections_2024_01 
PARTITION OF threat_detections 
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

### Caching Configuration
```yaml
# Redis optimization
redis:
  maxmemory: 2gb
  maxmemory-policy: allkeys-lru
  save: 900 1 300 10 60 10000
```

### Auto-scaling Setup
```bash
# Configure HPA
kubectl apply -f k8s/autoscaling.yaml

# Test auto-scaling
kubectl autoscale deployment threat-service \
  --cpu-percent=70 \
  --min=2 \
  --max=20 \
  -n cyber-sentinel
```

## 🚨 Troubleshooting

### Common Issues

#### Service Not Starting
```bash
# Check pod logs
kubectl logs -f deployment/threat-service -n cyber-sentinel

# Check events
kubectl describe pod <pod-name> -n cyber-sentinel

# Check resources
kubectl top pods -n cyber-sentinel
```

#### Database Connection Issues
```bash
# Test database connectivity
kubectl exec -it postgres-0 -n cyber-sentinel -- psql -U cyber_user

# Check connection pool
kubectl logs -f deployment/threat-service -n cyber-sentinel | grep "database"
```

#### Performance Issues
```bash
# Check response times
curl -w "@curl-format.txt" -o /dev/null -s https://api.cybersentinel.ai/health

# Monitor resources
kubectl top nodes
kubectl top pods -n cyber-sentinel
```

## 📋 Maintenance

### Regular Tasks
```bash
# Daily maintenance
./scripts/daily-maintenance.sh

# Weekly maintenance  
./scripts/weekly-maintenance.sh

# Monthly maintenance
./scripts/monthly-maintenance.sh
```

### Backup Procedures
```bash
# Database backup
kubectl exec -it postgres-0 -n cyber-sentinel -- pg_dump cyber_sentinel > backup.sql

# Configuration backup
kubectl get configmaps,secrets -n cyber-sentinel -o yaml > config-backup.yaml

# Full system backup
./scripts/backup-system.sh --environment production
```

### Update Procedures
```bash
# Rolling update
kubectl set image deployment/threat-service threat-service=cyber-sentinel/threat-service:v2.1.0

# Monitor rollout
kubectl rollout status deployment/threat-service -n cyber-sentinel

# Rollback if needed
kubectl rollout undo deployment/threat-service -n cyber-sentinel
```

## 📞 Support

### Monitoring Alerts
- **Critical**: System down, security breach
- **Warning**: High resource usage, performance degradation  
- **Info**: Deployments, configuration changes

### Escalation
1. **Level 1**: Automated monitoring and alerts
2. **Level 2**: On-call engineer (15 min response)
3. **Level 3**: Team lead (30 min response)
4. **Level 4**: Management (1 hour response)

### Contact
- **Emergency**: emergency@cybersentinel.ai
- **Support**: support@cybersentinel.ai
- **Slack**: #cyber-sentinel-support
- **Documentation**: https://docs.cybersentinel.ai

## 🎉 Success Metrics

After deployment, you should see:

### Performance Metrics
- **API Response Time**: < 100ms (P95)
- **Throughput**: 10K+ requests/second
- **Detection Latency**: < 200ms
- **System Availability**: 99.99%

### Security Metrics
- **Zero critical vulnerabilities**
- **All security controls enabled**
- **Compliance with SOC 2, ISO 27001**
- **Encryption at rest and in transit**

### Operational Metrics
- **Auto-scaling working**
- **Monitoring and alerting active**
- **Backup and recovery verified**
- **Documentation complete**

---

## 🚀 Next Steps

1. **Configure attack detection rules** for your environment
2. **Set up monitoring alerts** with your thresholds
3. **Train your team** on the system and procedures
4. **Plan regular maintenance** and update schedules
5. **Monitor performance** and optimize as needed

**Welcome to enterprise-grade network threat detection!** 🛡️

For additional support, see our comprehensive documentation at https://docs.cybersentinel.ai or contact our enterprise support team.
