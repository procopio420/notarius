# Terraform configuration for Notarius production deployment
# This file defines the main infrastructure components

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.1"
    }
  }
  
  backend "s3" {
    # Configure backend in terraform.tfvars or via environment variables
    # bucket = "notarius-terraform-state"
    # key    = "production/terraform.tfstate"
    # region = "us-east-1"
  }
}

# Configure the AWS Provider
provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "Notarius"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

# Local values
locals {
  name_prefix = "${var.project_name}-${var.environment}"
  
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
  
  # VPC CIDR blocks
  vpc_cidr = "10.0.0.0/16"
  
  # Subnet CIDR blocks
  public_subnet_cidrs  = ["10.0.1.0/24", "10.0.2.0/24"]
  private_subnet_cidrs = ["10.0.10.0/24", "10.0.20.0/24"]
  db_subnet_cidrs      = ["10.0.100.0/24", "10.0.200.0/24"]
  
  # Availability zones
  azs = slice(data.aws_availability_zones.available.names, 0, 2)
}

# VPC
module "vpc" {
  source = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"
  
  name = "${local.name_prefix}-vpc"
  cidr = local.vpc_cidr
  
  azs             = local.azs
  public_subnets  = local.public_subnet_cidrs
  private_subnets = local.private_subnet_cidrs
  database_subnets = local.db_subnet_cidrs
  
  enable_nat_gateway = true
  enable_vpn_gateway = false
  enable_dns_hostnames = true
  enable_dns_support = true
  
  public_subnet_tags = {
    Type = "public"
  }
  
  private_subnet_tags = {
    Type = "private"
  }
  
  database_subnet_tags = {
    Type = "database"
  }
  
  tags = local.common_tags
}

# Security Groups
module "security_groups" {
  source = "./modules/security-groups"
  
  name_prefix = local.name_prefix
  vpc_id      = module.vpc.vpc_id
  
  # Allow inbound traffic from ALB
  alb_security_group_id = module.alb.security_group_id
  
  tags = local.common_tags
}

# Application Load Balancer
module "alb" {
  source = "terraform-aws-modules/alb/aws"
  version = "~> 8.0"
  
  name = "${local.name_prefix}-alb"
  
  load_balancer_type = "application"
  
  vpc_id          = module.vpc.vpc_id
  subnets         = module.vpc.public_subnets
  security_groups = [module.security_groups.alb_security_group_id]
  
  # HTTP listener
  http_tcp_listeners = [
    {
      port               = 80
      protocol           = "HTTP"
      target_group_index = 0
    }
  ]
  
  # HTTPS listener (if SSL certificate is provided)
  https_listeners = var.ssl_certificate_arn != null ? [
    {
      port               = 443
      protocol           = "HTTPS"
      certificate_arn    = var.ssl_certificate_arn
      target_group_index = 0
    }
  ] : []
  
  # Target groups
  target_groups = [
    {
      name             = "${local.name_prefix}-tg"
      backend_protocol = "HTTP"
      backend_port     = 8000
      target_type      = "ip"
      
      health_check = {
        enabled             = true
        healthy_threshold   = 2
        interval            = 30
        matcher             = "200"
        path                = "/health/"
        port                = "traffic-port"
        protocol            = "HTTP"
        timeout             = 5
        unhealthy_threshold = 2
      }
      
      tags = local.common_tags
    }
  ]
  
  tags = local.common_tags
}

# ECS Cluster
module "ecs_cluster" {
  source = "./modules/ecs-cluster"
  
  name_prefix = local.name_prefix
  vpc_id      = module.vpc.vpc_id
  subnets     = module.vpc.private_subnets
  
  # ECS Cluster configuration
  cluster_name = "${local.name_prefix}-cluster"
  
  # ECS Service configuration
  service_name = "${local.name_prefix}-service"
  
  # Task definition configuration
  task_family = "${local.name_prefix}-task"
  
  # Container configurations
  containers = {
    notarius-api = {
      name  = "notarius-api"
      image = "${var.aws_account_id}.dkr.ecr.${var.aws_region}.amazonaws.com/notarius-api:latest"
      port  = 8000
      cpu   = 512
      memory = 1024
      environment_variables = {
        DJANGO_SETTINGS_MODULE = "notarius.settings.production"
        DATABASE_URL          = "postgresql://${module.rds.db_instance_username}:${module.rds.db_instance_password}@${module.rds.db_instance_endpoint}/${module.rds.db_instance_name}"
        REDIS_URL            = "redis://${module.elasticache.redis_endpoint}:6379"
        PII_VAULT_URL        = "http://${module.ecs_cluster.pii_vault_service_name}:8002"
        LEXNODE_API_URL      = "http://${module.ecs_cluster.lexnode_service_name}:8001"
        INTENT_ENGINE_URL    = "http://${module.ecs_cluster.intent_engine_service_name}:8003"
        S3_BUCKET_NAME       = module.s3.bucket_name
        KMS_KEY_ID          = module.kms.key_id
      }
      secrets = {
        SECRET_KEY = "${module.secrets_manager.secret_arn}:SECRET_KEY::"
        DATABASE_PASSWORD = "${module.secrets_manager.secret_arn}:DATABASE_PASSWORD::"
      }
    }
    
    pii-vault = {
      name  = "pii-vault"
      image = "${var.aws_account_id}.dkr.ecr.${var.aws_region}.amazonaws.com/pii-vault:latest"
      port  = 8002
      cpu   = 256
      memory = 512
      environment_variables = {
        DATABASE_URL = "postgresql://${module.rds.db_instance_username}:${module.rds.db_instance_password}@${module.rds.db_instance_endpoint}/${module.rds.db_instance_name}"
        KMS_KEY_ID   = module.kms.key_id
      }
      secrets = {
        SECRET_KEY = "${module.secrets_manager.secret_arn}:SECRET_KEY::"
      }
    }
    
    lexnode-api = {
      name  = "lexnode-api"
      image = "${var.aws_account_id}.dkr.ecr.${var.aws_region}.amazonaws.com/lexnode-api:latest"
      port  = 8001
      cpu   = 512
      memory = 1024
      environment_variables = {
        DATABASE_URL = "postgresql://${module.rds.db_instance_username}:${module.rds.db_instance_password}@${module.rds.db_instance_endpoint}/${module.rds.db_instance_name}"
        REDIS_URL    = "redis://${module.elasticache.redis_endpoint}:6379"
      }
      secrets = {
        SECRET_KEY = "${module.secrets_manager.secret_arn}:SECRET_KEY::"
      }
    }
    
    intent-engine = {
      name  = "intent-engine"
      image = "${var.aws_account_id}.dkr.ecr.${var.aws_region}.amazonaws.com/intent-engine:latest"
      port  = 8003
      cpu   = 512
      memory = 1024
      environment_variables = {
        DATABASE_URL = "postgresql://${module.rds.db_instance_username}:${module.rds.db_instance_password}@${module.rds.db_instance_endpoint}/${module.rds.db_instance_name}"
        REDIS_URL    = "redis://${module.elasticache.redis_endpoint}:6379"
      }
      secrets = {
        SECRET_KEY = "${module.secrets_manager.secret_arn}:SECRET_KEY::"
      }
    }
  }
  
  # Load balancer configuration
  target_group_arn = module.alb.target_group_arns[0]
  
  tags = local.common_tags
}

# RDS Database
module "rds" {
  source = "./modules/rds"
  
  name_prefix = local.name_prefix
  vpc_id      = module.vpc.vpc_id
  subnets     = module.vpc.database_subnets
  
  # Database configuration
  db_name     = "notarius"
  db_username = "notarius"
  db_password = var.db_password
  
  # Instance configuration
  instance_class = var.db_instance_class
  allocated_storage = var.db_allocated_storage
  max_allocated_storage = var.db_max_allocated_storage
  
  # Security
  vpc_security_group_ids = [module.security_groups.rds_security_group_id]
  
  tags = local.common_tags
}

# ElastiCache Redis
module "elasticache" {
  source = "./modules/elasticache"
  
  name_prefix = local.name_prefix
  vpc_id      = module.vpc.vpc_id
  subnets     = module.vpc.private_subnets
  
  # Redis configuration
  node_type = var.redis_node_type
  num_cache_nodes = var.redis_num_cache_nodes
  
  # Security
  vpc_security_group_ids = [module.security_groups.redis_security_group_id]
  
  tags = local.common_tags
}

# S3 Bucket
module "s3" {
  source = "./modules/s3"
  
  name_prefix = local.name_prefix
  
  # Bucket configuration
  bucket_name = "${local.name_prefix}-documents"
  
  # Versioning
  versioning_enabled = true
  
  # Encryption
  encryption_enabled = true
  kms_key_id = module.kms.key_id
  
  # Lifecycle
  lifecycle_rules = [
    {
      id      = "delete_old_versions"
      enabled = true
      noncurrent_version_expiration = {
        days = 30
      }
    }
  ]
  
  tags = local.common_tags
}

# KMS Key
module "kms" {
  source = "./modules/kms"
  
  name_prefix = local.name_prefix
  
  # Key configuration
  description = "KMS key for Notarius encryption"
  
  # Key policy
  key_usage = "ENCRYPT_DECRYPT"
  key_spec  = "SYMMETRIC_DEFAULT"
  
  tags = local.common_tags
}

# Secrets Manager
module "secrets_manager" {
  source = "./modules/secrets-manager"
  
  name_prefix = local.name_prefix
  
  # Secrets configuration
  secrets = {
    SECRET_KEY = var.secret_key
    DATABASE_PASSWORD = var.db_password
  }
  
  tags = local.common_tags
}

# CloudWatch Logs
module "cloudwatch_logs" {
  source = "./modules/cloudwatch-logs"
  
  name_prefix = local.name_prefix
  
  # Log groups
  log_groups = [
    {
      name              = "/aws/ecs/${local.name_prefix}"
      retention_in_days = 30
    },
    {
      name              = "/aws/ecs/${local.name_prefix}/notarius-api"
      retention_in_days = 30
    },
    {
      name              = "/aws/ecs/${local.name_prefix}/pii-vault"
      retention_in_days = 30
    },
    {
      name              = "/aws/ecs/${local.name_prefix}/lexnode-api"
      retention_in_days = 30
    },
    {
      name              = "/aws/ecs/${local.name_prefix}/intent-engine"
      retention_in_days = 30
    }
  ]
  
  tags = local.common_tags
}

# ECR Repositories
module "ecr" {
  source = "./modules/ecr"
  
  name_prefix = local.name_prefix
  
  # Repository configurations
  repositories = [
    {
      name = "notarius-api"
      image_tag_mutability = "MUTABLE"
      scan_on_push = true
    },
    {
      name = "pii-vault"
      image_tag_mutability = "MUTABLE"
      scan_on_push = true
    },
    {
      name = "lexnode-api"
      image_tag_mutability = "MUTABLE"
      scan_on_push = true
    },
    {
      name = "intent-engine"
      image_tag_mutability = "MUTABLE"
      scan_on_push = true
    }
  ]
  
  tags = local.common_tags
}

# IAM Roles
module "iam_roles" {
  source = "./modules/iam-roles"
  
  name_prefix = local.name_prefix
  
  # ECS Task Role
  ecs_task_role_policies = [
    {
      name = "S3Access"
      policy = jsonencode({
        Version = "2012-10-17"
        Statement = [
          {
            Effect = "Allow"
            Action = [
              "s3:GetObject",
              "s3:PutObject",
              "s3:DeleteObject"
            ]
            Resource = "${module.s3.bucket_arn}/*"
          }
        ]
      })
    },
    {
      name = "KMSAccess"
      policy = jsonencode({
        Version = "2012-10-17"
        Statement = [
          {
            Effect = "Allow"
            Action = [
              "kms:Encrypt",
              "kms:Decrypt",
              "kms:ReEncrypt*",
              "kms:GenerateDataKey*",
              "kms:DescribeKey"
            ]
            Resource = module.kms.key_arn
          }
        ]
      })
    },
    {
      name = "SecretsManagerAccess"
      policy = jsonencode({
        Version = "2012-10-17"
        Statement = [
          {
            Effect = "Allow"
            Action = [
              "secretsmanager:GetSecretValue"
            ]
            Resource = module.secrets_manager.secret_arn
          }
        ]
      })
    }
  ]
  
  tags = local.common_tags
}

# Outputs
output "vpc_id" {
  description = "ID of the VPC"
  value       = module.vpc.vpc_id
}

output "vpc_cidr_block" {
  description = "CIDR block of the VPC"
  value       = module.vpc.vpc_cidr_block
}

output "public_subnets" {
  description = "List of IDs of public subnets"
  value       = module.vpc.public_subnets
}

output "private_subnets" {
  description = "List of IDs of private subnets"
  value       = module.vpc.private_subnets
}

output "database_subnets" {
  description = "List of IDs of database subnets"
  value       = module.vpc.database_subnets
}

output "alb_dns_name" {
  description = "DNS name of the load balancer"
  value       = module.alb.lb_dns_name
}

output "alb_zone_id" {
  description = "Zone ID of the load balancer"
  value       = module.alb.lb_zone_id
}

output "ecs_cluster_id" {
  description = "ID of the ECS cluster"
  value       = module.ecs_cluster.cluster_id
}

output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = module.ecs_cluster.cluster_name
}

output "rds_endpoint" {
  description = "RDS instance endpoint"
  value       = module.rds.db_instance_endpoint
}

output "rds_port" {
  description = "RDS instance port"
  value       = module.rds.db_instance_port
}

output "redis_endpoint" {
  description = "Redis cluster endpoint"
  value       = module.elasticache.redis_endpoint
}

output "redis_port" {
  description = "Redis cluster port"
  value       = module.elasticache.redis_port
}

output "s3_bucket_name" {
  description = "Name of the S3 bucket"
  value       = module.s3.bucket_name
}

output "s3_bucket_arn" {
  description = "ARN of the S3 bucket"
  value       = module.s3.bucket_arn
}

output "kms_key_id" {
  description = "ID of the KMS key"
  value       = module.kms.key_id
}

output "kms_key_arn" {
  description = "ARN of the KMS key"
  value       = module.kms.key_arn
}

output "secrets_manager_secret_arn" {
  description = "ARN of the Secrets Manager secret"
  value       = module.secrets_manager.secret_arn
}

output "ecr_repository_urls" {
  description = "URLs of the ECR repositories"
  value       = module.ecr.repository_urls
}
