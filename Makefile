# Notarius Development Makefile
.PHONY: help setup start stop restart status logs test clean build deploy

# Default target
help: ## Show this help message
	@echo "Notarius Development Commands"
	@echo "============================="
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Development setup
setup: ## Complete development environment setup
	@echo "🚀 Setting up Notarius development environment..."
	@./scripts/dev-setup.sh setup

start: ## Start all services
	@echo "▶️  Starting services..."
	@./scripts/dev-setup.sh start

stop: ## Stop all services
	@echo "⏹️  Stopping services..."
	@./scripts/dev-setup.sh stop

restart: ## Restart all services
	@echo "🔄 Restarting services..."
	@./scripts/dev-setup.sh restart

status: ## Show service status and URLs
	@./scripts/dev-setup.sh status

logs: ## Show logs for all services
	@./scripts/dev-setup.sh logs

# Development commands
shell: ## Open shell in API container
	@docker-compose exec notarius-api bash

migrate: ## Run database migrations
	@echo "🗄️  Running database migrations..."
	@docker-compose exec notarius-api python manage.py migrate
	@docker-compose exec notarius-api python manage.py collectstatic --noinput

createsuperuser: ## Create Django superuser
	@docker-compose exec notarius-api python manage.py createsuperuser

# Testing
test: ## Run all tests
	@echo "🧪 Running tests..."
	@python tests/run_all_tests.py --quick

test-full: ## Run full test suite
	@echo "🧪 Running full test suite..."
	@python tests/run_all_tests.py --all

test-unit: ## Run unit tests only
	@echo "🧪 Running unit tests..."
	@python tests/run_all_tests.py --test-types unit

test-integration: ## Run integration tests only
	@echo "🧪 Running integration tests..."
	@python tests/run_all_tests.py --test-types integration

test-e2e: ## Run end-to-end tests only
	@echo "🧪 Running E2E tests..."
	@python tests/run_all_tests.py --test-types e2e

test-security: ## Run security tests only
	@echo "🔒 Running security tests..."
	@python tests/run_all_tests.py --test-types security

test-performance: ## Run performance tests only
	@echo "⚡ Running performance tests..."
	@python tests/run_all_tests.py --test-types performance

# Code quality
lint: ## Run linting checks
	@echo "🔍 Running linting checks..."
	@python tests/run_all_tests.py --test-types linting

type-check: ## Run type checking
	@echo "🔍 Running type checking..."
	@python tests/run_all_tests.py --test-types type-checking

format: ## Format code with black and isort
	@echo "🎨 Formatting code..."
	@find . -name "*.py" -not -path "./venv/*" -not -path "./.git/*" | xargs black
	@find . -name "*.py" -not -path "./venv/*" -not -path "./.git/*" | xargs isort

# Docker commands
build: ## Build all Docker images
	@echo "🔨 Building Docker images..."
	@docker-compose build --parallel

build-no-cache: ## Build all Docker images without cache
	@echo "🔨 Building Docker images (no cache)..."
	@docker-compose build --no-cache --parallel

pull: ## Pull latest images
	@echo "⬇️  Pulling latest images..."
	@docker-compose pull

# Database commands
db-reset: ## Reset all databases
	@echo "🗄️  Resetting databases..."
	@docker-compose down -v
	@docker-compose up -d postgres-notarius postgres-lexnode postgres-vault redis
	@sleep 10
	@make migrate

db-backup: ## Backup all databases
	@echo "💾 Backing up databases..."
	@mkdir -p backups
	@docker-compose exec postgres-notarius pg_dump -U notarius notarius_db > backups/notarius_db_$(shell date +%Y%m%d_%H%M%S).sql
	@docker-compose exec postgres-lexnode pg_dump -U lexnode lexnode_db > backups/lexnode_db_$(shell date +%Y%m%d_%H%M%S).sql
	@docker-compose exec postgres-vault pg_dump -U vault vault_db > backups/vault_db_$(shell date +%Y%m%d_%H%M%S).sql

# Monitoring
monitor: ## Open monitoring dashboards
	@echo "📊 Opening monitoring dashboards..."
	@echo "Grafana: http://localhost:3001 (admin/admin)"
	@echo "Prometheus: http://localhost:9090"
	@echo "Jaeger: http://localhost:16686"

# Cleanup
clean: ## Clean up containers and volumes
	@echo "🧹 Cleaning up..."
	@./scripts/dev-setup.sh cleanup

clean-all: ## Clean up everything including images
	@echo "🧹 Cleaning up everything..."
	@docker-compose down -v --rmi all
	@docker system prune -f

# Deployment
deploy-local: ## Deploy to local environment using Ansible
	@echo "🚀 Deploying to local environment..."
	@ansible-playbook ansible/playbooks/deploy-local.yml

deploy-staging: ## Deploy to staging environment using Ansible
	@echo "🚀 Deploying to staging environment..."
	@ansible-playbook ansible/playbooks/deploy-staging.yml

deploy-production: ## Deploy to production environment using Ansible
	@echo "🚀 Deploying to production environment..."
	@ansible-playbook ansible/playbooks/deploy-production.yml

# Security
security-scan: ## Run security scans
	@echo "🔒 Running security scans..."
	@bandit -r apps/ packages/
	@safety check
	@python tests/run_all_tests.py --test-types security

# Documentation
docs: ## Generate documentation
	@echo "📚 Generating documentation..."
	@cd docs && make html

# Development workflow
dev: setup start ## Quick development setup (setup + start)
	@echo "✅ Development environment ready!"

ci: test lint type-check security-scan ## Run CI pipeline locally
	@echo "✅ CI pipeline completed successfully!"

# Service-specific commands
api-logs: ## Show API logs
	@docker-compose logs -f notarius-api

lexnode-logs: ## Show LexNode logs
	@docker-compose logs -f lexnode-api

pii-vault-logs: ## Show PII Vault logs
	@docker-compose logs -f pii-vault

intent-engine-logs: ## Show Intent Engine logs
	@docker-compose logs -f intent-engine

web-logs: ## Show Web UI logs
	@docker-compose logs -f notarius-web

# Database service commands
db-notarius: ## Connect to Notarius database
	@docker-compose exec postgres-notarius psql -U notarius -d notarius_db

db-lexnode: ## Connect to LexNode database
	@docker-compose exec postgres-lexnode psql -U lexnode -d lexnode_db

db-vault: ## Connect to PII Vault database
	@docker-compose exec postgres-vault psql -U vault -d vault_db

# Redis commands
redis-cli: ## Connect to Redis CLI
	@docker-compose exec redis redis-cli

# Health checks
health: ## Check health of all services
	@echo "🏥 Checking service health..."
	@echo ""
	@echo "Core Services:"
	@curl -s http://localhost:3000 > /dev/null && echo "  ✅ Frontend (Next.js):     http://localhost:3000" || echo "  ❌ Frontend: FAIL"
	@curl -s http://localhost:8000/admin/ > /dev/null && echo "  ✅ Django API:             http://localhost:8000" || echo "  ❌ Django API: FAIL"
	@curl -s http://localhost:8001/health/ > /dev/null && echo "  ✅ LexNode RAG:            http://localhost:8001" || echo "  ❌ LexNode: FAIL"
	@curl -s http://localhost:8002/health/ > /dev/null && echo "  ✅ PII Vault:              http://localhost:8002" || echo "  ❌ PII Vault: FAIL"
	@curl -s http://localhost:8003/health/ > /dev/null && echo "  ✅ Intent Engine:          http://localhost:8003" || echo "  ❌ Intent Engine: FAIL"
	@echo ""
	@echo "Monitoring:"
	@curl -s http://localhost:3001 > /dev/null && echo "  ✅ Grafana:                http://localhost:3001 (admin/admin)" || echo "  ❌ Grafana: FAIL"
	@curl -s http://localhost:9090 > /dev/null && echo "  ✅ Prometheus:             http://localhost:9090" || echo "  ❌ Prometheus: FAIL"
	@curl -s http://localhost:16686 > /dev/null && echo "  ✅ Jaeger:                 http://localhost:16686" || echo "  ❌ Jaeger: FAIL"
	@echo ""
	@echo "Development Tools:"
	@curl -s http://localhost:8025 > /dev/null && echo "  ✅ MailHog (Email):        http://localhost:8025" || echo "  ❌ MailHog: FAIL"
	@curl -s http://localhost:9001 > /dev/null && echo "  ✅ MinIO (S3 Storage):     http://localhost:9001 (minioadmin/minioadmin)" || echo "  ❌ MinIO: FAIL"
	@echo ""
	@echo "📊 Total Services Running: $$(docker-compose ps | grep -c Up)/14"

# Quick commands
quick-start: ## Quick start for development
	@make dev
	@make health

quick-test: ## Quick test run
	@make test
	@make health

# Environment info
env-info: ## Show environment information
	@echo "Environment Information"
	@echo "======================"
	@echo "Docker version: $(shell docker --version)"
	@echo "Docker Compose version: $(shell docker-compose --version)"
	@echo "Python version: $(shell python3 --version)"
	@echo "Node version: $(shell node --version 2>/dev/null || echo 'Not installed')"
	@echo "Git version: $(shell git --version)"
	@echo "Current directory: $(shell pwd)"
	@echo "Environment file: $(shell test -f .env && echo '✅ .env exists' || echo '❌ .env missing')"

