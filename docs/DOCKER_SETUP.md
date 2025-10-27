# Docker Setup Guide

This guide covers the comprehensive Docker setup for the Notarius monorepo, including local development, staging, and production environments.

## Overview

The Notarius project uses Docker for containerization with the following architecture:

- **Multi-stage Dockerfiles** for optimized builds
- **Docker Compose** for orchestration
- **Ansible** for infrastructure management
- **Development tools** for local development
- **Production optimizations** for scalability

## Quick Start

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- Make (optional, for convenience commands)
- Ansible 2.9+ (for infrastructure management)

### Local Development Setup

1. **Clone and setup:**
   ```bash
   git clone <repository-url>
   cd notarius
   make setup
   ```

2. **Or use the setup script directly:**
   ```bash
   ./scripts/dev-setup.sh setup
   ```

3. **Access the application:**
   - Web UI: http://localhost:3000
   - API: http://localhost:8000
   - Grafana: http://localhost:3001 (admin/admin)

## Docker Architecture

### Services Overview

| Service | Port | Description |
|---------|------|-------------|
| notarius-api | 8000 | Django REST API |
| lexnode-api | 8001 | Legal document processing |
| pii-vault | 8002 | PII storage and tokenization |
| intent-engine | 8003 | AI intent processing |
| notarius-web | 3000 | Next.js frontend |
| postgres-notarius | 5432 | Main database |
| postgres-lexnode | 5433 | Legal documents database |
| postgres-vault | 5434 | PII vault database |
| redis | 6379 | Cache and queues |
| grafana | 3001 | Monitoring dashboard |
| prometheus | 9090 | Metrics collection |
| jaeger | 16686 | Distributed tracing |
| mailhog | 8025 | Email testing |
| minio | 9001 | S3-compatible storage |

### Multi-Stage Dockerfiles

Each service uses multi-stage Dockerfiles for optimization:

```dockerfile
# Development stage
FROM python:3.11-slim as development
# ... development setup

# Production stage  
FROM python:3.11-slim as production
# ... production optimizations
```

**Benefits:**
- Smaller production images
- Development tools in dev stage only
- Security hardening in production
- Non-root users for security

## Environment Configuration

### Environment Files

- `.env` - Local development (auto-generated)
- `docker-compose.override.yml` - Development overrides
- `docker-compose.prod.yml` - Production configuration

### Key Environment Variables

```bash
# Database URLs
DATABASE_URL=postgresql://notarius:notarius_dev@localhost:5432/notarius_db
LEXNODE_DATABASE_URL=postgresql://lexnode:lexnode_dev@localhost:5433/lexnode_db
VAULT_DATABASE_URL=postgresql://vault:vault_dev@localhost:5434/vault_db

# Service URLs
PII_VAULT_URL=http://localhost:8002
INTENT_ENGINE_URL=http://localhost:8003
LEXNODE_URL=http://localhost:8001

# AI Services
OPENAI_API_KEY=your-openai-api-key-here

# Storage (MinIO for development)
AWS_S3_ENDPOINT_URL=http://localhost:9000
AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=minioadmin
```

## Development Workflow

### Using Make Commands

```bash
# Complete setup
make setup

# Start services
make start

# View logs
make logs

# Run tests
make test

# Open shell in API container
make shell

# Check service health
make health

# Stop services
make stop

# Clean up
make clean
```

### Using Docker Compose Directly

```bash
# Start all services
docker-compose up -d

# Start specific service
docker-compose up -d notarius-api

# View logs
docker-compose logs -f notarius-api

# Run commands in container
docker-compose exec notarius-api python manage.py migrate

# Stop services
docker-compose down

# Rebuild and restart
docker-compose up -d --build
```

### Development Tools

**MailHog** - Email testing
- URL: http://localhost:8025
- SMTP: localhost:1025

**MinIO** - S3-compatible storage
- Console: http://localhost:9001
- Credentials: minioadmin/minioadmin

**Grafana** - Monitoring
- URL: http://localhost:3001
- Credentials: admin/admin

**Jaeger** - Distributed tracing
- URL: http://localhost:16686

## Production Deployment

### Using Ansible

1. **Configure inventory:**
   ```bash
   # Edit ansible/inventory/hosts.yml
   # Add your production servers
   ```

2. **Deploy to staging:**
   ```bash
   make deploy-staging
   # or
   ansible-playbook ansible/playbooks/deploy-staging.yml
   ```

3. **Deploy to production:**
   ```bash
   make deploy-production
   # or
   ansible-playbook ansible/playbooks/deploy-production.yml
   ```

### Production Optimizations

**Resource Limits:**
```yaml
deploy:
  resources:
    limits:
      memory: 1G
      cpus: '0.5'
    reservations:
      memory: 512M
      cpus: '0.25'
```

**Health Checks:**
```dockerfile
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1
```

**Security:**
- Non-root users
- Read-only filesystems where possible
- Minimal base images
- Security scanning

## Monitoring and Observability

### Metrics Collection

**Prometheus** collects metrics from:
- Application services
- Database connections
- Redis performance
- System resources

**Grafana Dashboards:**
- Application performance
- Database metrics
- System resources
- Business metrics

### Logging

**Structured Logging:**
- JSON format for production
- Correlation IDs
- PII redaction
- Log aggregation

**Log Levels:**
- DEBUG: Development
- INFO: Production
- ERROR: Critical issues

### Distributed Tracing

**Jaeger** provides:
- Request tracing across services
- Performance analysis
- Error debugging
- Service dependency mapping

## Database Management

### Migrations

```bash
# Run migrations
make migrate

# Or directly
docker-compose exec notarius-api python manage.py migrate
```

### Backups

```bash
# Create backup
make db-backup

# Restore from backup
docker-compose exec postgres-notarius psql -U notarius -d notarius_db < backup.sql
```

### Database Access

```bash
# Connect to databases
make db-notarius    # Main database
make db-lexnode     # Legal documents
make db-vault       # PII vault
```

## Testing in Docker

### Running Tests

```bash
# Quick tests
make test

# Full test suite
make test-full

# Specific test types
make test-unit
make test-integration
make test-e2e
make test-security
make test-performance
```

### Test Configuration

- **In-memory databases** for speed
- **Mock services** for external dependencies
- **Parallel execution** for performance
- **Coverage reporting** for quality

## Troubleshooting

### Common Issues

**Services not starting:**
```bash
# Check logs
docker-compose logs notarius-api

# Check health
make health

# Restart services
make restart
```

**Database connection issues:**
```bash
# Check database status
docker-compose ps postgres-notarius

# Test connection
docker-compose exec postgres-notarius pg_isready -U notarius
```

**Port conflicts:**
```bash
# Check port usage
netstat -tulpn | grep :8000

# Change ports in docker-compose.yml
```

### Debugging

**Container shell access:**
```bash
# API container
make shell

# Database container
docker-compose exec postgres-notarius bash

# Redis container
make redis-cli
```

**Service logs:**
```bash
# All services
make logs

# Specific service
make api-logs
make lexnode-logs
make pii-vault-logs
```

## Performance Optimization

### Development

- **Volume mounts** for live code reloading
- **Development tools** (debug toolbar, profiling)
- **Hot reloading** for frontend

### Production

- **Multi-stage builds** for smaller images
- **Resource limits** for stability
- **Health checks** for reliability
- **Scaling** with Docker Swarm or Kubernetes

### Monitoring

- **Prometheus metrics** for performance tracking
- **Grafana dashboards** for visualization
- **Alerting** for proactive monitoring

## Security Considerations

### Development

- **Local-only services** (no external exposure)
- **Development credentials** (not for production)
- **Debug mode** enabled

### Production

- **Non-root users** in containers
- **Read-only filesystems** where possible
- **Security scanning** in CI/CD
- **Secrets management** with external tools
- **Network isolation** between services

## Best Practices

### Development

1. **Use Make commands** for common tasks
2. **Check service health** regularly
3. **Run tests** before committing
4. **Use development tools** for debugging
5. **Keep environment files** up to date

### Production

1. **Use multi-stage builds** for optimization
2. **Set resource limits** for stability
3. **Enable health checks** for monitoring
4. **Use secrets management** for credentials
5. **Monitor performance** continuously

### Maintenance

1. **Regular updates** of base images
2. **Security scanning** of containers
3. **Backup strategies** for data
4. **Monitoring** of resource usage
5. **Documentation** of changes

## Support

For issues and questions:

1. **Check logs** first: `make logs`
2. **Verify health**: `make health`
3. **Review documentation**: This guide and API docs
4. **Check GitHub issues**: For known problems
5. **Create new issue**: For new problems

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Ansible Documentation](https://docs.ansible.com/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)

