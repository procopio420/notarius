#!/bin/bash

# Notarius Local Development Setup Script
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="notarius"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$PROJECT_DIR/.env"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_requirements() {
    log_info "Checking requirements..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check Git
    if ! command -v git &> /dev/null; then
        log_error "Git is not installed. Please install Git first."
        exit 1
    fi
    
    log_success "All requirements are met"
}

create_env_file() {
    log_info "Creating environment file..."
    
    if [ ! -f "$ENV_FILE" ]; then
        cat > "$ENV_FILE" << EOF
# Notarius Development Environment
DEBUG=True
SECRET_KEY=dev-secret-key-change-in-production

# Database URLs
DATABASE_URL=postgresql://notarius:notarius_dev@localhost:5432/notarius_db
LEXNODE_DATABASE_URL=postgresql://lexnode:lexnode_dev@localhost:5433/lexnode_db
VAULT_DATABASE_URL=postgresql://vault:vault_dev@localhost:5434/vault_db

# Redis
REDIS_URL=redis://localhost:6379/0

# Service URLs
PII_VAULT_URL=http://localhost:8002
INTENT_ENGINE_URL=http://localhost:8003
LEXNODE_URL=http://localhost:8001

# AI Services
OPENAI_API_KEY=your-openai-api-key-here

# Email (MailHog for development)
EMAIL_HOST=localhost
EMAIL_PORT=1025
EMAIL_USE_TLS=False

# Storage (MinIO for development)
AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=minioadmin
AWS_STORAGE_BUCKET_NAME=notarius-dev
AWS_S3_ENDPOINT_URL=http://localhost:9000

# Monitoring
GRAFANA_ADMIN_PASSWORD=admin
PROMETHEUS_RETENTION=7d

# Security
KMS_PROVIDER=local
KMS_KEY_ID=dev-key
EOF
        log_success "Environment file created at $ENV_FILE"
        log_warning "Please update the OPENAI_API_KEY in $ENV_FILE"
    else
        log_info "Environment file already exists"
    fi
}

setup_docker_networks() {
    log_info "Setting up Docker networks..."
    
    # Create custom network for Notarius
    docker network create notarius-network 2>/dev/null || log_info "Network notarius-network already exists"
    
    log_success "Docker networks configured"
}

build_images() {
    log_info "Building Docker images..."
    
    cd "$PROJECT_DIR"
    
    # Build all services
    docker-compose build --parallel
    
    log_success "Docker images built successfully"
}

start_services() {
    log_info "Starting services..."
    
    cd "$PROJECT_DIR"
    
    # Start infrastructure services first
    docker-compose up -d postgres-notarius postgres-lexnode postgres-vault redis
    
    # Wait for databases to be ready
    log_info "Waiting for databases to be ready..."
    sleep 10
    
    # Start application services
    docker-compose up -d notarius-api lexnode-api pii-vault intent-engine
    
    # Wait for APIs to be ready
    log_info "Waiting for APIs to be ready..."
    sleep 15
    
    # Start web frontend
    docker-compose up -d notarius-web
    
    # Start monitoring stack
    docker-compose up -d grafana prometheus jaeger
    
    # Start development tools
    log_info "Starting development tools (MailHog for email testing, MinIO for S3 storage)..."
    docker-compose up -d mailhog minio
    
    log_success "All services started"
}

run_migrations() {
    log_info "Running database migrations..."
    
    cd "$PROJECT_DIR"
    
    # Run Django migrations
    docker-compose exec notarius-api python manage.py migrate
    
    # Create superuser (skip if already exists)
    docker-compose exec -T notarius-api python manage.py shell -c "
from django.contrib.auth import get_user_model;
User = get_user_model();
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@notarius.com', 'admin')
    print('Superuser created')
else:
    print('Superuser already exists')
" 2>/dev/null || true
    
    # Collect static files (skip if STATIC_ROOT not set)
    docker-compose exec notarius-api python manage.py collectstatic --noinput 2>/dev/null || log_info "Skipped collectstatic (STATIC_ROOT not configured for dev)"
    
    log_success "Database migrations completed"
}

show_status() {
    log_info "Service Status:"
    echo ""
    
    cd "$PROJECT_DIR"
    docker-compose ps
    
    echo ""
    log_info "Access URLs:"
    echo "  🌐 Web UI:          http://localhost:3000"
    echo "  🔧 API:             http://localhost:8000"
    echo "  📚 LexNode:         http://localhost:8001"
    echo "  🔐 PII Vault:       http://localhost:8002"
    echo "  🤖 Intent Engine:    http://localhost:8003"
    echo "  📊 Grafana:         http://localhost:3001 (admin/admin)"
    echo "  📈 Prometheus:      http://localhost:9090"
    echo "  🔍 Jaeger:          http://localhost:16686"
    echo ""
    echo "  Development Tools:"
    echo "  📧 MailHog:         http://localhost:8025 (email testing)"
    echo "  💾 MinIO:           http://localhost:9001 (S3 storage - minioadmin/minioadmin)"
    echo ""
    log_info "Admin credentials:"
    echo "  Username: admin"
    echo "  Email: admin@notarius.com"
    echo "  Password: (set via Django admin or create new superuser)"
}

run_tests() {
    log_info "Running tests..."
    
    cd "$PROJECT_DIR"
    
    # Run comprehensive test suite
    python tests/run_all_tests.py --quick
    
    log_success "Tests completed"
}

cleanup() {
    log_info "Cleaning up..."
    
    cd "$PROJECT_DIR"
    
    # Stop and remove containers
    docker-compose down -v
    
    # Remove images (optional)
    read -p "Do you want to remove Docker images? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose down --rmi all
    fi
    
    log_success "Cleanup completed"
}

show_help() {
    echo "Notarius Development Setup Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  setup     - Complete development environment setup"
    echo "  start     - Start all services"
    echo "  stop      - Stop all services"
    echo "  restart   - Restart all services"
    echo "  status    - Show service status and URLs"
    echo "  logs      - Show logs for all services"
    echo "  test      - Run test suite"
    echo "  migrate   - Run database migrations"
    echo "  shell     - Open shell in API container"
    echo "  cleanup   - Stop services and clean up"
    echo "  help      - Show this help message"
    echo ""
}

# Main script logic
case "${1:-setup}" in
    setup)
        log_info "Setting up Notarius development environment..."
        check_requirements
        create_env_file
        setup_docker_networks
        build_images
        start_services
        run_migrations
        show_status
        log_success "Development environment setup complete!"
        ;;
    start)
        log_info "Starting services..."
        start_services
        show_status
        ;;
    stop)
        log_info "Stopping services..."
        cd "$PROJECT_DIR"
        docker-compose down
        log_success "Services stopped"
        ;;
    restart)
        log_info "Restarting services..."
        cd "$PROJECT_DIR"
        docker-compose restart
        show_status
        ;;
    status)
        show_status
        ;;
    logs)
        cd "$PROJECT_DIR"
        docker-compose logs -f
        ;;
    test)
        run_tests
        ;;
    migrate)
        run_migrations
        ;;
    shell)
        cd "$PROJECT_DIR"
        docker-compose exec notarius-api bash
        ;;
    cleanup)
        cleanup
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        log_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac

