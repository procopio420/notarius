# Variables for Notarius Terraform configuration

# General variables
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "aws_account_id" {
  description = "AWS account ID"
  type        = string
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "notarius"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

# VPC variables
variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
  default     = []
}

# Database variables
variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "db_allocated_storage" {
  description = "RDS allocated storage in GB"
  type        = number
  default     = 20
}

variable "db_max_allocated_storage" {
  description = "RDS maximum allocated storage in GB"
  type        = number
  default     = 100
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

variable "db_username" {
  description = "Database username"
  type        = string
  default     = "notarius"
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "notarius"
}

# Redis variables
variable "redis_node_type" {
  description = "ElastiCache Redis node type"
  type        = string
  default     = "cache.t3.micro"
}

variable "redis_num_cache_nodes" {
  description = "Number of cache nodes"
  type        = number
  default     = 1
}

# ECS variables
variable "ecs_task_cpu" {
  description = "CPU units for ECS task"
  type        = number
  default     = 512
}

variable "ecs_task_memory" {
  description = "Memory for ECS task in MB"
  type        = number
  default     = 1024
}

variable "ecs_desired_count" {
  description = "Desired number of ECS tasks"
  type        = number
  default     = 2
}

variable "ecs_min_capacity" {
  description = "Minimum number of ECS tasks"
  type        = number
  default     = 1
}

variable "ecs_max_capacity" {
  description = "Maximum number of ECS tasks"
  type        = number
  default     = 10
}

# Load Balancer variables
variable "ssl_certificate_arn" {
  description = "ARN of SSL certificate for HTTPS"
  type        = string
  default     = null
}

variable "domain_name" {
  description = "Domain name for the application"
  type        = string
  default     = null
}

# S3 variables
variable "s3_bucket_name" {
  description = "Name of the S3 bucket"
  type        = string
  default     = null
}

variable "s3_versioning_enabled" {
  description = "Enable S3 versioning"
  type        = bool
  default     = true
}

variable "s3_encryption_enabled" {
  description = "Enable S3 encryption"
  type        = bool
  default     = true
}

# KMS variables
variable "kms_key_description" {
  description = "Description for KMS key"
  type        = string
  default     = "KMS key for Notarius encryption"
}

variable "kms_key_usage" {
  description = "Usage for KMS key"
  type        = string
  default     = "ENCRYPT_DECRYPT"
}

variable "kms_key_spec" {
  description = "Spec for KMS key"
  type        = string
  default     = "SYMMETRIC_DEFAULT"
}

# Secrets Manager variables
variable "secret_key" {
  description = "Secret key for Django"
  type        = string
  sensitive   = true
}

variable "secrets_rotation_days" {
  description = "Number of days for secrets rotation"
  type        = number
  default     = 30
}

# CloudWatch variables
variable "log_retention_days" {
  description = "Number of days to retain logs"
  type        = number
  default     = 30
}

variable "enable_cloudwatch_alarms" {
  description = "Enable CloudWatch alarms"
  type        = bool
  default     = true
}

# Monitoring variables
variable "enable_monitoring" {
  description = "Enable monitoring and alerting"
  type        = bool
  default     = true
}

variable "monitoring_email" {
  description = "Email for monitoring alerts"
  type        = string
  default     = null
}

# Backup variables
variable "enable_backups" {
  description = "Enable automated backups"
  type        = bool
  default     = true
}

variable "backup_retention_days" {
  description = "Number of days to retain backups"
  type        = number
  default     = 7
}

variable "backup_window" {
  description = "Backup window"
  type        = string
  default     = "03:00-04:00"
}

variable "maintenance_window" {
  description = "Maintenance window"
  type        = string
  default     = "sun:04:00-sun:05:00"
}

# Security variables
variable "enable_encryption_at_rest" {
  description = "Enable encryption at rest"
  type        = bool
  default     = true
}

variable "enable_encryption_in_transit" {
  description = "Enable encryption in transit"
  type        = bool
  default     = true
}

variable "enable_vpc_flow_logs" {
  description = "Enable VPC flow logs"
  type        = bool
  default     = true
}

# Networking variables
variable "enable_nat_gateway" {
  description = "Enable NAT Gateway"
  type        = bool
  default     = true
}

variable "enable_vpn_gateway" {
  description = "Enable VPN Gateway"
  type        = bool
  default     = false
}

variable "enable_dns_hostnames" {
  description = "Enable DNS hostnames"
  type        = bool
  default     = true
}

variable "enable_dns_support" {
  description = "Enable DNS support"
  type        = bool
  default     = true
}

# Auto Scaling variables
variable "enable_auto_scaling" {
  description = "Enable auto scaling"
  type        = bool
  default     = true
}

variable "auto_scaling_scale_up_cooldown" {
  description = "Scale up cooldown in seconds"
  type        = number
  default     = 300
}

variable "auto_scaling_scale_down_cooldown" {
  description = "Scale down cooldown in seconds"
  type        = number
  default     = 300
}

variable "auto_scaling_target_cpu_utilization" {
  description = "Target CPU utilization for auto scaling"
  type        = number
  default     = 70
}

variable "auto_scaling_target_memory_utilization" {
  description = "Target memory utilization for auto scaling"
  type        = number
  default     = 80
}

# Container variables
variable "container_image_tag" {
  description = "Tag for container images"
  type        = string
  default     = "latest"
}

variable "container_health_check_grace_period" {
  description = "Health check grace period in seconds"
  type        = number
  default     = 300
}

variable "container_deployment_maximum_percent" {
  description = "Maximum percent for deployment"
  type        = number
  default     = 200
}

variable "container_deployment_minimum_healthy_percent" {
  description = "Minimum healthy percent for deployment"
  type        = number
  default     = 100
}

# Environment-specific variables
variable "django_debug" {
  description = "Django debug mode"
  type        = bool
  default     = false
}

variable "django_allowed_hosts" {
  description = "Django allowed hosts"
  type        = list(string)
  default     = ["*"]
}

variable "django_cors_allowed_origins" {
  description = "Django CORS allowed origins"
  type        = list(string)
  default     = []
}

variable "django_cors_allowed_credentials" {
  description = "Django CORS allowed credentials"
  type        = bool
  default     = true
}

# Feature flags
variable "enable_pii_vault" {
  description = "Enable PII Vault service"
  type        = bool
  default     = true
}

variable "enable_lexnode" {
  description = "Enable LexNode service"
  type        = bool
  default     = true
}

variable "enable_intent_engine" {
  description = "Enable Intent Engine service"
  type        = bool
  default     = true
}

variable "enable_observability" {
  description = "Enable observability stack"
  type        = bool
  default     = true
}

# Cost optimization variables
variable "enable_spot_instances" {
  description = "Enable spot instances for cost optimization"
  type        = bool
  default     = false
}

variable "enable_scheduled_scaling" {
  description = "Enable scheduled scaling"
  type        = bool
  default     = false
}

variable "scheduled_scaling_schedule" {
  description = "Schedule for scaling"
  type        = string
  default     = "cron(0 8 * * MON-FRI)"
}

# Compliance variables
variable "enable_compliance_monitoring" {
  description = "Enable compliance monitoring"
  type        = bool
  default     = true
}

variable "compliance_retention_days" {
  description = "Compliance retention days"
  type        = number
  default     = 2555  # 7 years
}

variable "enable_audit_logging" {
  description = "Enable audit logging"
  type        = bool
  default     = true
}

# Disaster recovery variables
variable "enable_multi_az" {
  description = "Enable multi-AZ deployment"
  type        = bool
  default     = true
}

variable "enable_cross_region_backup" {
  description = "Enable cross-region backup"
  type        = bool
  default     = false
}

variable "backup_region" {
  description = "Region for cross-region backup"
  type        = string
  default     = null
}

# Performance variables
variable "enable_performance_insights" {
  description = "Enable RDS Performance Insights"
  type        = bool
  default     = true
}

variable "performance_insights_retention_days" {
  description = "Performance Insights retention days"
  type        = number
  default     = 7
}

variable "enable_enhanced_monitoring" {
  description = "Enable RDS enhanced monitoring"
  type        = bool
  default     = true
}

variable "enhanced_monitoring_interval" {
  description = "Enhanced monitoring interval in seconds"
  type        = number
  default     = 60
}
