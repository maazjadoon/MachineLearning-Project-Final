#!/bin/bash

# Cyber Sentinel ML - Enterprise Deployment Script
# FAANG-grade deployment automation

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CONFIG_FILE="$PROJECT_ROOT/config/deployment.env"
LOG_FILE="$PROJECT_ROOT/logs/deployment-$(date +%Y%m%d-%H%M%S).log"

# Default values
ENVIRONMENT="staging"
REGION="us-west-2"
CLUSTER_NAME="cyber-sentinel-cluster"
NAMESPACE="cyber-sentinel"
DRY_RUN=false
SKIP_TESTS=false
FORCE_DEPLOY=false

# Load configuration
if [[ -f "$CONFIG_FILE" ]]; then
    source "$CONFIG_FILE"
fi

# Logging function
log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case $level in
        "INFO")
            echo -e "${GREEN}[INFO]${NC} $message" | tee -a "$LOG_FILE"
            ;;
        "WARN")
            echo -e "${YELLOW}[WARN]${NC} $message" | tee -a "$LOG_FILE"
            ;;
        "ERROR")
            echo -e "${RED}[ERROR]${NC} $message" | tee -a "$LOG_FILE"
            ;;
        "DEBUG")
            echo -e "${BLUE}[DEBUG]${NC} $message" | tee -a "$LOG_FILE"
            ;;
    esac
    
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
}

# Function to check prerequisites
check_prerequisites() {
    log "INFO" "Checking prerequisites..."
    
    # Check required tools
    local required_tools=("kubectl" "helm" "docker" "aws" "terraform" "k6")
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log "ERROR" "Required tool $tool is not installed"
            exit 1
        fi
    done
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        log "ERROR" "AWS credentials not configured"
        exit 1
    fi
    
    # Check kubectl connection
    if ! kubectl cluster-info &> /dev/null; then
        log "ERROR" "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    # Check Docker registry access
    if ! docker info &> /dev/null; then
        log "ERROR" "Cannot access Docker registry"
        exit 1
    fi
    
    log "INFO" "All prerequisites satisfied"
}

# Function to validate environment
validate_environment() {
    log "INFO" "Validating environment: $ENVIRONMENT"
    
    case $ENVIRONMENT in
        "development"|"staging"|"production")
            ;;
        *)
            log "ERROR" "Invalid environment: $ENVIRONMENT"
            exit 1
            ;;
    esac
    
    # Check if namespace exists
    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log "WARN" "Namespace $NAMESPACE does not exist"
        if [[ "$FORCE_DEPLOY" == "true" ]]; then
            log "INFO" "Creating namespace $NAMESPACE"
            kubectl create namespace "$NAMESPACE"
        else
            log "ERROR" "Namespace $NAMESPACE not found. Use --force to create"
            exit 1
        fi
    fi
    
    log "INFO" "Environment validation completed"
}

# Function to build and push images
build_and_push_images() {
    log "INFO" "Building and pushing Docker images..."
    
    local registry="${DOCKER_REGISTRY:-ghcr.io}"
    local tag="${IMAGE_TAG:-$(git rev-parse --short HEAD)}"
    local project_name="cyber-sentinel"
    
    # Services to build
    local services=(
        "threat-service:Dockerfile.threat"
        "ml-service:Dockerfile.ml"
        "analytics-service:Dockerfile.analytics"
        "config-service:Dockerfile.config"
    )
    
    for service in "${services[@]}"; do
        IFS=':' read -r service_name dockerfile <<< "$service"
        
        log "INFO" "Building $service_name..."
        
        if [[ "$DRY_RUN" == "true" ]]; then
            log "DEBUG" "Would build: $service_name with $dockerfile"
            continue
        fi
        
        # Build image
        docker build \
            -f "$dockerfile" \
            -t "$registry/$project_name/$service_name:$tag" \
            -t "$registry/$project_name/$service_name:latest" \
            "$PROJECT_ROOT"
        
        # Push image
        docker push "$registry/$project_name/$service_name:$tag"
        docker push "$registry/$project_name/$service_name:latest"
        
        log "INFO" "Successfully built and pushed $service_name"
    done
    
    # Build frontend
    log "INFO" "Building frontend..."
    cd "$PROJECT_ROOT/frontend"
    docker build \
        -t "$registry/$project_name/web-frontend:$tag" \
        -t "$registry/$project_name/web-frontend:latest" \
        .
    docker push "$registry/$project_name/web-frontend:$tag"
    docker push "$registry/$project_name/web-frontend:latest"
    cd "$PROJECT_ROOT"
    
    log "INFO" "All images built and pushed successfully"
}

# Function to run tests
run_tests() {
    if [[ "$SKIP_TESTS" == "true" ]]; then
        log "WARN" "Skipping tests as requested"
        return 0
    fi
    
    log "INFO" "Running pre-deployment tests..."
    
    # Unit tests
    log "INFO" "Running unit tests..."
    if ! pytest tests/unit/ -v --cov=. --cov-report=term-missing; then
        log "ERROR" "Unit tests failed"
        exit 1
    fi
    
    # Integration tests
    log "INFO" "Running integration tests..."
    if ! pytest tests/integration/ -v; then
        log "ERROR" "Integration tests failed"
        exit 1
    fi
    
    # Load tests
    log "INFO" "Running load tests..."
    if ! k6 run tests/load/smoke.js; then
        log "ERROR" "Load tests failed"
        exit 1
    fi
    
    log "INFO" "All tests passed successfully"
}

# Function to deploy infrastructure
deploy_infrastructure() {
    log "INFO" "Deploying infrastructure..."
    
    cd "$PROJECT_ROOT/terraform"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "DEBUG" "Would run: terraform plan"
        cd "$PROJECT_ROOT"
        return 0
    fi
    
    # Initialize Terraform
    terraform init
    
    # Plan deployment
    terraform plan -var="environment=$ENVIRONMENT" -var="region=$REGION"
    
    # Apply changes
    terraform apply -var="environment=$ENVIRONMENT" -var="region=$REGION" -auto-approve
    
    cd "$PROJECT_ROOT"
    log "INFO" "Infrastructure deployed successfully"
}

# Function to deploy Kubernetes resources
deploy_kubernetes() {
    log "INFO" "Deploying Kubernetes resources..."
    
    local tag="${IMAGE_TAG:-$(git rev-parse --short HEAD)}"
    local registry="${DOCKER_REGISTRY:-ghcr.io}"
    local project_name="cyber-sentinel"
    
    # Update image tags in deployment files
    sed -i.bak "s|image: cyber-sentinel/|image: $registry/$project_name/|g" "$PROJECT_ROOT/k8s/deployments.yaml"
    sed -i.bak "s|:latest|:$tag|g" "$PROJECT_ROOT/k8s/deployments.yaml"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "DEBUG" "Would apply Kubernetes manifests"
        kubectl apply --dry-run=client -f "$PROJECT_ROOT/k8s/" -n "$NAMESPACE"
        # Restore backup
        mv "$PROJECT_ROOT/k8s/deployments.yaml.bak" "$PROJECT_ROOT/k8s/deployments.yaml"
        return 0
    fi
    
    # Apply Kubernetes manifests
    kubectl apply -f "$PROJECT_ROOT/k8s/namespace.yaml"
    kubectl apply -f "$PROJECT_ROOT/k8s/secrets.yaml"
    kubectl apply -f "$PROJECT_ROOT/k8s/configmap.yaml"
    kubectl apply -f "$PROJECT_ROOT/k8s/deployments.yaml"
    kubectl apply -f "$PROJECT_ROOT/k8s/services.yaml"
    kubectl apply -f "$PROJECT_ROOT/k8s/autoscaling.yaml"
    
    # Wait for deployments to be ready
    log "INFO" "Waiting for deployments to be ready..."
    kubectl wait --for=condition=available --timeout=600s deployment --all -n "$NAMESPACE"
    
    # Restore backup
    mv "$PROJECT_ROOT/k8s/deployments.yaml.bak" "$PROJECT_ROOT/k8s/deployments.yaml"
    
    log "INFO" "Kubernetes resources deployed successfully"
}

# Function to deploy monitoring
deploy_monitoring() {
    log "INFO" "Deploying monitoring stack..."
    
    # Deploy Prometheus
    kubectl apply -f "$PROJECT_ROOT/monitoring/prometheus/" -n "$NAMESPACE-monitoring"
    
    # Deploy Grafana
    kubectl apply -f "$PROJECT_ROOT/monitoring/grafana/" -n "$NAMESPACE-monitoring"
    
    # Deploy Jaeger
    kubectl apply -f "$PROJECT_ROOT/monitoring/jaeger/" -n "$NAMESPACE-monitoring"
    
    # Wait for monitoring stack
    kubectl wait --for=condition=available --timeout=300s deployment --all -n "$NAMESPACE-monitoring"
    
    log "INFO" "Monitoring stack deployed successfully"
}

# Function to run post-deployment tests
run_post_deployment_tests() {
    log "INFO" "Running post-deployment tests..."
    
    # Get service URLs
    local api_url=$(kubectl get ingress cyber-sentinel-ingress -n "$NAMESPACE" -o jsonpath='{.spec.rules[0].host}')
    local monitoring_url=$(kubectl get ingress monitoring-ingress -n "$NAMESPACE-monitoring" -o jsonpath='{.spec.rules[0].host}')
    
    # Health checks
    log "INFO" "Running health checks..."
    if ! curl -f "https://$api_url/health" --max-time 30; then
        log "ERROR" "Health check failed for API"
        exit 1
    fi
    
    # API functionality tests
    log "INFO" "Running API functionality tests..."
    if ! curl -f "https://$api_url/api/v1/threat/stats" --max-time 30; then
        log "ERROR" "API functionality test failed"
        exit 1
    fi
    
    # Performance tests
    log "INFO" "Running performance tests..."
    if ! k6 run tests/performance/post-deployment.js --max-time 120; then
        log "ERROR" "Performance tests failed"
        exit 1
    fi
    
    log "INFO" "Post-deployment tests passed successfully"
    
    # Output access information
    log "INFO" "Deployment completed successfully!"
    log "INFO" "API URL: https://$api_url"
    log "INFO" "Monitoring URL: https://$monitoring_url"
    log "INFO" "Grafana Dashboard: https://$monitoring_url/grafana"
    log "INFO" "Jaeger Tracing: https://$monitoring_url/jaeger"
}

# Function to rollback deployment
rollback_deployment() {
    log "WARN" "Rolling back deployment..."
    
    # Get previous revision
    local previous_revision=$(kubectl rollout history deployment/threat-service -n "$NAMESPACE" | tail -2 | head -1 | awk '{print $1}')
    
    if [[ -z "$previous_revision" ]]; then
        log "ERROR" "No previous revision found for rollback"
        exit 1
    fi
    
    # Rollback all deployments
    local deployments=("threat-service" "ml-service" "analytics-service" "config-service" "web-frontend")
    
    for deployment in "${deployments[@]}"; do
        log "INFO" "Rolling back $deployment to revision $previous_revision"
        kubectl rollout undo deployment/"$deployment" -n "$NAMESPACE"
        kubectl rollout status deployment/"$deployment" -n "$NAMESPACE" --timeout=300s
    done
    
    log "INFO" "Rollback completed successfully"
}

# Function to cleanup resources
cleanup() {
    log "INFO" "Cleaning up temporary resources..."
    
    # Remove temporary files
    rm -f "$PROJECT_ROOT/k8s/deployments.yaml.bak"
    
    # Clean up Docker images (optional)
    if [[ "${CLEANUP_DOCKER:-false}" == "true" ]]; then
        log "INFO" "Cleaning up Docker images..."
        docker system prune -f
    fi
    
    log "INFO" "Cleanup completed"
}

# Function to show usage
show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Enterprise deployment script for Cyber Sentinel ML

OPTIONS:
    -e, --environment ENV    Deployment environment (development|staging|production)
    -r, --region REGION      AWS region (default: us-west-2)
    -n, --namespace NAMESPACE Kubernetes namespace (default: cyber-sentinel)
    -t, --tag TAG            Docker image tag (default: git short hash)
    --dry-run                Show what would be deployed without actually deploying
    --skip-tests             Skip pre-deployment tests
    --force                  Force creation of namespace and other resources
    --rollback               Rollback to previous deployment
    --cleanup                Clean up temporary resources after deployment
    --help                   Show this help message

EXAMPLES:
    $0 --environment staging
    $0 --environment production --tag v1.2.3
    $0 --dry-run --environment staging
    $0 --rollback --environment production

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -r|--region)
            REGION="$2"
            shift 2
            ;;
        -n|--namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        -t|--tag)
            IMAGE_TAG="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --force)
            FORCE_DEPLOY=true
            shift
            ;;
        --rollback)
            ROLLBACK=true
            shift
            ;;
        --cleanup)
            CLEANUP_DOCKER=true
            shift
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            log "ERROR" "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Main deployment flow
main() {
    log "INFO" "Starting Cyber Sentinel ML enterprise deployment..."
    log "INFO" "Environment: $ENVIRONMENT"
    log "INFO" "Region: $REGION"
    log "INFO" "Namespace: $NAMESPACE"
    log "INFO" "Dry run: $DRY_RUN"
    
    # Create logs directory
    mkdir -p "$PROJECT_ROOT/logs"
    
    # Trap for cleanup
    trap cleanup EXIT
    
    # Check if rollback is requested
    if [[ "${ROLLBACK:-false}" == "true" ]]; then
        rollback_deployment
        exit 0
    fi
    
    # Deployment flow
    check_prerequisites
    validate_environment
    run_tests
    build_and_push_images
    deploy_infrastructure
    deploy_kubernetes
    deploy_monitoring
    run_post_deployment_tests
    
    log "INFO" "Enterprise deployment completed successfully! 🎉"
}

# Run main function
main "$@"
