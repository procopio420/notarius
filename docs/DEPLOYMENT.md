# Deployment Guide

This guide covers deployment strategies for the Notarius system, from local development to production environments.

## Deployment Overview

Notarius supports multiple deployment strategies:

- **Local Development**: Docker Compose for full-stack development
- **Staging**: Kubernetes with managed services
- **Production**: Cloud-native deployment with high availability

## Local Development Deployment

### Docker Compose Setup

**docker-compose.yml**:
```yaml
version: '3.8'

services:
  # Databases
  postgres-notarius:
    image: postgres:16
    environment:
      POSTGRES_DB: notarius_db
      POSTGRES_USER: notarius
      POSTGRES_PASSWORD: notarius123
    volumes:
      - postgres_notarius_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  postgres-lexnode:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: lexnode_db
      POSTGRES_USER: lexnode
      POSTGRES_PASSWORD: lexnode123
    volumes:
      - postgres_lexnode_data:/var/lib/postgresql/data
    ports:
      - "5433:5432"

  postgres-vault:
    image: postgres:16
    environment:
      POSTGRES_DB: vault_db
      POSTGRES_USER: vault
      POSTGRES_PASSWORD: vault123
    volumes:
      - postgres_vault_data:/var/lib/postgresql/data
    ports:
      - "5434:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  # Application Services
  notarius-api:
    build: ./apps/notarius-api
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://notarius:notarius123@postgres-notarius:5432/notarius_db
      - REDIS_URL=redis://redis:6379/0
      - DEBUG=True
    depends_on:
      - postgres-notarius
      - redis
    volumes:
      - ./apps/notarius-api:/app
      - ./media:/app/media

  lexnode-api:
    build: ./apps/lexnode-api
    ports:
      - "8001:8000"
    environment:
      - DATABASE_URL=postgresql://lexnode:lexnode123@postgres-lexnode:5432/lexnode_db
      - REDIS_URL=redis://redis:6379/1
    depends_on:
      - postgres-lexnode
      - redis

  pii-vault:
    build: ./apps/pii-vault
    ports:
      - "8002:8000"
    environment:
      - DATABASE_URL=postgresql://vault:vault123@postgres-vault:5432/vault_db
      - KMS_PROVIDER=local
    depends_on:
      - postgres-vault

  intent-engine:
    build: ./apps/intent-engine
    ports:
      - "8003:8000"
    environment:
      - PII_VAULT_URL=http://pii-vault:8000
      - LEXNODE_URL=http://lexnode-api:8000
      - REDIS_URL=redis://redis:6379/2
    depends_on:
      - pii-vault
      - lexnode-api
      - redis

  notarius-web:
    build: ./apps/notarius-web
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    depends_on:
      - notarius-api

  # Infrastructure Services
  traefik:
    image: traefik:v3.0
    ports:
      - "80:80"
      - "8080:8080"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./infra/traefik/traefik.yml:/etc/traefik/traefik.yml

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin123
    volumes:
      - grafana_data:/var/lib/grafana
      - ./infra/grafana/dashboards:/etc/grafana/provisioning/dashboards

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./infra/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus

volumes:
  postgres_notarius_data:
  postgres_lexnode_data:
  postgres_vault_data:
  grafana_data:
  prometheus_data:
```

**Deployment Commands**:
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f notarius-api

# Scale services
docker-compose up -d --scale notarius-api=3

# Stop services
docker-compose down

# Clean up volumes
docker-compose down -v
```

## Staging Deployment

### Kubernetes Setup

**namespace.yaml**:
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: notarius-staging
  labels:
    environment: staging
```

**configmap.yaml**:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: notarius-config
  namespace: notarius-staging
data:
  DATABASE_URL: "postgresql://user:pass@postgres:5432/notarius_db"
  REDIS_URL: "redis://redis:6379/0"
  DEBUG: "False"
  ALLOWED_HOSTS: "staging.notarius.ai"
```

**deployment.yaml**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: notarius-api
  namespace: notarius-staging
spec:
  replicas: 3
  selector:
    matchLabels:
      app: notarius-api
  template:
    metadata:
      labels:
        app: notarius-api
    spec:
      containers:
      - name: notarius-api
        image: notarius-api:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: notarius-config
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health/
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready/
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

**service.yaml**:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: notarius-api
  namespace: notarius-staging
spec:
  selector:
    app: notarius-api
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
```

**ingress.yaml**:
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: notarius-ingress
  namespace: notarius-staging
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - staging.notarius.ai
    secretName: notarius-tls
  rules:
  - host: staging.notarius.ai
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: notarius-api
            port:
              number: 80
```

**Deployment Commands**:
```bash
# Apply configurations
kubectl apply -f k8s/staging/

# Check deployment status
kubectl get pods -n notarius-staging

# View logs
kubectl logs -f deployment/notarius-api -n notarius-staging

# Scale deployment
kubectl scale deployment notarius-api --replicas=5 -n notarius-staging
```

## Production Deployment

### Infrastructure as Code (Terraform)

**main.tf**:
```hcl
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# VPC
module "vpc" {
  source = "terraform-aws-modules/vpc/aws"
  
  name = "${var.project_name}-vpc"
  cidr = "10.0.0.0/16"
  
  azs             = ["${var.aws_region}a", "${var.aws_region}b", "${var.aws_region}c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]
  
  enable_nat_gateway = true
  enable_vpn_gateway = true
  
  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

# ECS Cluster
resource "aws_ecs_cluster" "notarius" {
  name = "${var.project_name}-cluster"
  
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
  
  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

# RDS Database
module "rds" {
  source = "./modules/rds"
  
  project_name = var.project_name
  environment  = var.environment
  
  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets
  
  db_name     = "notarius"
  db_username = "notarius"
  db_password = var.db_password
  
  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

# ElastiCache Redis
resource "aws_elasticache_subnet_group" "notarius" {
  name       = "${var.project_name}-cache-subnet"
  subnet_ids = module.vpc.private_subnets
}

resource "aws_elasticache_replication_group" "notarius" {
  replication_group_id       = "${var.project_name}-redis"
  description                = "Redis cluster for Notarius"
  
  node_type                  = "cache.t3.micro"
  port                       = 6379
  parameter_group_name       = "default.redis7"
  
  num_cache_clusters         = 2
  automatic_failover_enabled = true
  multi_az_enabled          = true
  
  subnet_group_name = aws_elasticache_subnet_group.notarius.name
  security_group_ids = [aws_security_group.redis.id]
  
  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

# S3 Bucket
resource "aws_s3_bucket" "notarius" {
  bucket = "${var.project_name}-${var.environment}-storage"
  
  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_s3_bucket_versioning" "notarius" {
  bucket = aws_s3_bucket.notarius.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_encryption" "notarius" {
  bucket = aws_s3_bucket.notarius.id
  
  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "AES256"
      }
    }
  }
}

# KMS Key
resource "aws_kms_key" "notarius" {
  description             = "KMS key for Notarius PII encryption"
  deletion_window_in_days = 7
  
  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_kms_alias" "notarius" {
  name          = "alias/${var.project_name}-pii-key"
  target_key_id = aws_kms_key.notarius.key_id
}
```

**variables.tf**:
```hcl
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "notarius"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}
```

**Deployment Commands**:
```bash
# Initialize Terraform
terraform init

# Plan deployment
terraform plan -var="db_password=your-secure-password"

# Apply infrastructure
terraform apply -var="db_password=your-secure-password"

# Get outputs
terraform output
```

### Application Deployment

**Dockerfile**:
```dockerfile
# Multi-stage build for Django API
FROM python:3.11-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash notarius
RUN chown -R notarius:notarius /app
USER notarius

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health/ || exit 1

# Start application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "config.wsgi:application"]
```

**ECS Task Definition**:
```json
{
  "family": "notarius-api",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::account:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "notarius-api",
      "image": "your-account.dkr.ecr.region.amazonaws.com/notarius-api:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "DATABASE_URL",
          "value": "postgresql://user:pass@rds-endpoint:5432/notarius"
        },
        {
          "name": "REDIS_URL",
          "value": "redis://elasticache-endpoint:6379/0"
        }
      ],
      "secrets": [
        {
          "name": "SECRET_KEY",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:notarius/secret-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/notarius-api",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health/ || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
```

## CI/CD Pipeline

### GitHub Actions

**.github/workflows/deploy.yml**:
```yaml
name: Deploy to Production

on:
  push:
    branches: [main]
  workflow_dispatch:

env:
  AWS_REGION: us-east-1
  ECR_REGISTRY: ${{ secrets.AWS_ACCOUNT_ID }}.dkr.ecr.us-east-1.amazonaws.com
  ECS_SERVICE: notarius-api
  ECS_CLUSTER: notarius-cluster
  ECS_TASK_DEFINITION: notarius-api

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r apps/notarius-api/requirements.txt
          pip install pytest pytest-cov
      
      - name: Run tests
        run: |
          cd apps/notarius-api
          pytest --cov=apps --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./apps/notarius-api/coverage.xml

  build-and-deploy:
    needs: test
    runs-on: ubuntu-latest
    environment: production
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}
      
      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v1
      
      - name: Build, tag, and push image
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker build -t $ECR_REGISTRY/notarius-api:$IMAGE_TAG ./apps/notarius-api
          docker push $ECR_REGISTRY/notarius-api:$IMAGE_TAG
          docker tag $ECR_REGISTRY/notarius-api:$IMAGE_TAG $ECR_REGISTRY/notarius-api:latest
          docker push $ECR_REGISTRY/notarius-api:latest
      
      - name: Download task definition
        run: |
          aws ecs describe-task-definition \
            --task-definition $ECS_TASK_DEFINITION \
            --query taskDefinition > task-definition.json
      
      - name: Fill in the new image ID
        id: task-def
        uses: aws-actions/amazon-ecs-render-task-definition@v1
        with:
          task-definition: task-definition.json
          container-name: notarius-api
          image: ${{ steps.login-ecr.outputs.registry }}/notarius-api:${{ github.sha }}
      
      - name: Deploy Amazon ECS task definition
        uses: aws-actions/amazon-ecs-deploy-task-definition@v1
        with:
          task-definition: ${{ steps.task-def.outputs.task-definition }}
          service: ${{ env.ECS_SERVICE }}
          cluster: ${{ env.ECS_CLUSTER }}
          wait-for-service-stability: true
```

## Monitoring and Observability

### Application Monitoring

**Prometheus Configuration**:
```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'notarius-api'
    static_configs:
      - targets: ['notarius-api:8000']
    metrics_path: '/metrics'
    scrape_interval: 5s

  - job_name: 'lexnode-api'
    static_configs:
      - targets: ['lexnode-api:8000']
    metrics_path: '/metrics'

  - job_name: 'pii-vault'
    static_configs:
      - targets: ['pii-vault:8000']
    metrics_path: '/metrics'
```

**Grafana Dashboard**:
```json
{
  "dashboard": {
    "title": "Notarius System Overview",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{service}}"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      }
    ]
  }
}
```

### Log Management

**CloudWatch Logs Configuration**:
```yaml
# cloudwatch-logs.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluent-bit-config
data:
  fluent-bit.conf: |
    [SERVICE]
        Flush         1
        Log_Level     info
        Daemon        off
        Parsers_File  parsers.conf
        HTTP_Server   On
        HTTP_Listen   0.0.0.0
        HTTP_Port     2020

    [INPUT]
        Name              tail
        Path              /var/log/containers/*notarius*.log
        Parser            docker
        Tag               kube.*
        Refresh_Interval  5
        Mem_Buf_Limit     50MB
        Skip_Long_Lines   On

    [OUTPUT]
        Name                cloudwatch_logs
        Match               *
        region              us-east-1
        log_group_name      /aws/ecs/notarius
        log_stream_prefix   ecs-
        auto_create_group   true
```

## Security Considerations

### Network Security

**Security Groups**:
```hcl
# Security group for ECS tasks
resource "aws_security_group" "ecs_tasks" {
  name_prefix = "${var.project_name}-ecs-tasks-"
  vpc_id      = module.vpc.vpc_id

  ingress {
    protocol    = "tcp"
    from_port   = 8000
    to_port     = 8000
    cidr_blocks = [module.vpc.vpc_cidr_block]
  }

  egress {
    protocol    = "-1"
    from_port   = 0
    to_port     = 0
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.project_name}-ecs-tasks"
    Environment = var.environment
  }
}
```

### Secrets Management

**AWS Secrets Manager**:
```bash
# Store secrets
aws secretsmanager create-secret \
  --name "notarius/database-password" \
  --description "Database password for Notarius" \
  --secret-string "your-secure-password"

aws secretsmanager create-secret \
  --name "notarius/secret-key" \
  --description "Django secret key" \
  --secret-string "your-django-secret-key"
```

### SSL/TLS Configuration

**Certificate Manager**:
```hcl
# SSL certificate
resource "aws_acm_certificate" "notarius" {
  domain_name       = var.domain_name
  validation_method = "DNS"

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }

  lifecycle {
    create_before_destroy = true
  }
}
```

## Backup and Disaster Recovery

### Database Backups

**Automated RDS Backups**:
```hcl
resource "aws_db_instance" "notarius" {
  # ... other configuration ...
  
  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
  
  # Enable automated backups
  backup_retention_period = 30
  backup_window          = "03:00-04:00"
  
  # Enable point-in-time recovery
  enabled_cloudwatch_logs_exports = ["postgresql"]
}
```

### Application Data Backups

**S3 Lifecycle Policy**:
```hcl
resource "aws_s3_bucket_lifecycle_configuration" "notarius" {
  bucket = aws_s3_bucket.notarius.id

  rule {
    id     = "backup_retention"
    status = "Enabled"

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    transition {
      days          = 365
      storage_class = "DEEP_ARCHIVE"
    }
  }
}
```

## Performance Optimization

### Auto Scaling

**ECS Auto Scaling**:
```hcl
resource "aws_appautoscaling_target" "ecs_target" {
  max_capacity       = 10
  min_capacity       = 2
  resource_id        = "service/${aws_ecs_cluster.notarius.name}/${aws_ecs_service.notarius.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "ecs_policy_cpu" {
  name               = "cpu-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs_target.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_target.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value = 70.0
  }
}
```

### Caching Strategy

**ElastiCache Configuration**:
```hcl
resource "aws_elasticache_replication_group" "notarius" {
  # ... other configuration ...
  
  # Enable cluster mode for horizontal scaling
  cluster_mode {
    num_node_groups         = 2
    replicas_per_node_group = 1
  }
  
  # Configure memory optimization
  parameter_group_name = "default.redis7.cluster.on"
}
```

## Troubleshooting

### Common Deployment Issues

**Database Connection Issues**:
```bash
# Check database connectivity
kubectl exec -it deployment/notarius-api -- python manage.py dbshell

# Check database status
kubectl logs deployment/notarius-api | grep -i database
```

**Memory Issues**:
```bash
# Check memory usage
kubectl top pods

# Check resource limits
kubectl describe pod notarius-api-xxx
```

**Network Issues**:
```bash
# Check service endpoints
kubectl get endpoints

# Test connectivity
kubectl exec -it deployment/notarius-api -- curl http://redis:6379
```

### Monitoring Commands

```bash
# Check application health
curl http://localhost:8000/health/

# Check metrics
curl http://localhost:8000/metrics

# View logs
kubectl logs -f deployment/notarius-api

# Check resource usage
kubectl top nodes
kubectl top pods
```

---

This deployment guide provides a comprehensive approach to deploying Notarius in various environments, from local development to production-scale deployments.
