#!/bin/bash

# Deploy script for Notarius services
# Usage: ./deploy.sh [environment] [service]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT="staging"
SERVICE="all"
VERSION="latest"
DRY_RUN=false
FORCE=false

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -e, --environment ENV    Environment to deploy to (staging|production) [default: staging]"
    echo "  -s, --service SERVICE    Service to deploy (notarius-api|pii-vault|lexnode-api|intent-engine|all) [default: all]"
    echo "  -v, --version VERSION    Version to deploy [default: latest]"
    echo "  -d, --dry-run           Show what would be deployed without actually deploying"
    echo "  -f, --force             Force deployment even if checks fail"
    echo "  -h, --help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Deploy all services to staging"
    echo "  $0 -e production -s notarius-api     # Deploy notarius-api to production"
    echo "  $0 -v v1.2.3 -d                      # Dry run deployment of v1.2.3"
    echo "  $0 -e production -f                  # Force deploy to production"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -s|--service)
            SERVICE="$2"
            shift 2
            ;;
        -v|--version)
            VERSION="$2"
            shift 2
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -f|--force)
            FORCE=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Validate environment
if [[ "$ENVIRONMENT" != "staging" && "$ENVIRONMENT" != "production" ]]; then
    print_error "Invalid environment: $ENVIRONMENT. Must be 'staging' or 'production'"
    exit 1
fi

# Validate service
if [[ "$SERVICE" != "all" && "$SERVICE" != "notarius-api" && "$SERVICE" != "pii-vault" && "$SERVICE" != "lexnode-api" && "$SERVICE" != "intent-engine" ]]; then
    print_error "Invalid service: $SERVICE. Must be 'all', 'notarius-api', 'pii-vault', 'lexnode-api', or 'intent-engine'"
    exit 1
fi

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if Docker is installed and running
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        print_error "Docker is not running"
        exit 1
    fi
    
    # Check if kubectl is installed
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl is not installed"
        exit 1
    fi
    
    # Check if helm is installed
    if ! command -v helm &> /dev/null; then
        print_error "Helm is not installed"
        exit 1
    fi
    
    # Check if terraform is installed
    if ! command -v terraform &> /dev/null; then
        print_error "Terraform is not installed"
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Function to check environment connectivity
check_connectivity() {
    print_status "Checking environment connectivity..."
    
    # Check kubectl connectivity
    if ! kubectl cluster-info &> /dev/null; then
        print_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    # Check AWS connectivity
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "Cannot connect to AWS"
        exit 1
    fi
    
    print_success "Connectivity check passed"
}

# Function to check service health
check_service_health() {
    local service_name=$1
    print_status "Checking health of $service_name..."
    
    # Get service status
    local status=$(kubectl get pods -l app=$service_name -o jsonpath='{.items[0].status.phase}' 2>/dev/null || echo "NotFound")
    
    if [[ "$status" == "Running" ]]; then
        print_success "$service_name is healthy"
        return 0
    elif [[ "$status" == "NotFound" ]]; then
        print_warning "$service_name is not deployed"
        return 1
    else
        print_warning "$service_name is in state: $status"
        return 1
    fi
}

# Function to deploy infrastructure
deploy_infrastructure() {
    print_status "Deploying infrastructure for $ENVIRONMENT..."
    
    cd infra/terraform
    
    # Initialize Terraform
    terraform init
    
    # Plan deployment
    terraform plan -var-file="${ENVIRONMENT}.tfvars" -var="container_image_tag=$VERSION"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        print_warning "Dry run: Infrastructure deployment would be executed"
        return 0
    fi
    
    # Apply deployment
    terraform apply -var-file="${ENVIRONMENT}.tfvars" -var="container_image_tag=$VERSION" -auto-approve
    
    print_success "Infrastructure deployed successfully"
    cd ../..
}

# Function to deploy service
deploy_service() {
    local service_name=$1
    print_status "Deploying $service_name to $ENVIRONMENT..."
    
    # Check if Helm chart exists
    local chart_path="infra/helm/$service_name"
    if [[ ! -d "$chart_path" ]]; then
        print_error "Helm chart not found: $chart_path"
        return 1
    fi
    
    # Update Helm chart version
    if [[ "$VERSION" != "latest" ]]; then
        python3 scripts/update-helm-charts.py "$VERSION"
    fi
    
    # Deploy with Helm
    local release_name="$service_name-$ENVIRONMENT"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        print_warning "Dry run: $service_name deployment would be executed"
        helm upgrade --install "$release_name" "$chart_path" \
            --namespace "$ENVIRONMENT" \
            --create-namespace \
            --set image.tag="$VERSION" \
            --dry-run
    else
        helm upgrade --install "$release_name" "$chart_path" \
            --namespace "$ENVIRONMENT" \
            --create-namespace \
            --set image.tag="$VERSION" \
            --wait \
            --timeout=10m
        
        print_success "$service_name deployed successfully"
    fi
}

# Function to run health checks
run_health_checks() {
    print_status "Running health checks..."
    
    local services=("notarius-api" "pii-vault" "lexnode-api" "intent-engine")
    local failed_services=()
    
    for service in "${services[@]}"; do
        if [[ "$SERVICE" == "all" || "$SERVICE" == "$service" ]]; then
            if ! check_service_health "$service"; then
                failed_services+=("$service")
            fi
        fi
    done
    
    if [[ ${#failed_services[@]} -gt 0 ]]; then
        print_error "Health checks failed for: ${failed_services[*]}"
        if [[ "$FORCE" != "true" ]]; then
            exit 1
        fi
    else
        print_success "All health checks passed"
    fi
}

# Function to run smoke tests
run_smoke_tests() {
    print_status "Running smoke tests..."
    
    # Get service URLs
    local notarius_url=$(kubectl get service notarius-api -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "localhost:8000")
    
    # Run basic health check
    if curl -f "http://$notarius_url/health/" &> /dev/null; then
        print_success "Smoke tests passed"
    else
        print_error "Smoke tests failed"
        if [[ "$FORCE" != "true" ]]; then
            exit 1
        fi
    fi
}

# Function to rollback deployment
rollback_deployment() {
    print_status "Rolling back deployment..."
    
    local services=("notarius-api" "pii-vault" "lexnode-api" "intent-engine")
    
    for service in "${services[@]}"; do
        if [[ "$SERVICE" == "all" || "$SERVICE" == "$service" ]]; then
            local release_name="$service-$ENVIRONMENT"
            helm rollback "$release_name" --namespace "$ENVIRONMENT"
            print_success "$service rolled back"
        fi
    done
}

# Function to cleanup resources
cleanup_resources() {
    print_status "Cleaning up resources..."
    
    # Clean up temporary files
    rm -f /tmp/notarius-deploy-*
    
    print_success "Cleanup completed"
}

# Main deployment function
main() {
    print_status "Starting deployment to $ENVIRONMENT"
    print_status "Service: $SERVICE"
    print_status "Version: $VERSION"
    print_status "Dry run: $DRY_RUN"
    print_status "Force: $FORCE"
    
    # Set up error handling
    trap cleanup_resources EXIT
    
    # Run checks
    check_prerequisites
    check_connectivity
    
    # Deploy infrastructure
    deploy_infrastructure
    
    # Deploy services
    if [[ "$SERVICE" == "all" ]]; then
        local services=("notarius-api" "pii-vault" "lexnode-api" "intent-engine")
        for service in "${services[@]}"; do
            deploy_service "$service"
        done
    else
        deploy_service "$SERVICE"
    fi
    
    # Run post-deployment checks
    if [[ "$DRY_RUN" != "true" ]]; then
        run_health_checks
        run_smoke_tests
    fi
    
    print_success "Deployment completed successfully!"
    
    # Show deployment summary
    echo ""
    print_status "Deployment Summary:"
    echo "  Environment: $ENVIRONMENT"
    echo "  Service: $SERVICE"
    echo "  Version: $VERSION"
    echo "  Status: Success"
    
    if [[ "$ENVIRONMENT" == "production" ]]; then
        echo ""
        print_warning "Production deployment completed. Monitor the system closely."
    fi
}

# Run main function
main "$@"
