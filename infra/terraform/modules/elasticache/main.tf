# ElastiCache module for Notarius

# ElastiCache Subnet Group
resource "aws_elasticache_subnet_group" "main" {
  name       = "${var.name_prefix}-cache-subnet-group"
  subnet_ids = var.subnets
  
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-cache-subnet-group"
  })
}

# ElastiCache Parameter Group
resource "aws_elasticache_parameter_group" "main" {
  family = "redis7.x"
  name   = "${var.name_prefix}-cache-parameter-group"
  
  parameter {
    name  = "maxmemory-policy"
    value = "allkeys-lru"
  }
  
  parameter {
    name  = "timeout"
    value = "300"
  }
  
  tags = var.tags
}

# ElastiCache Replication Group
resource "aws_elasticache_replication_group" "main" {
  replication_group_id       = "${var.name_prefix}-redis"
  description                = "Redis cluster for Notarius"
  
  # Engine
  engine               = "redis"
  engine_version       = "7.0"
  parameter_group_name = aws_elasticache_parameter_group.main.name
  
  # Instance
  node_type            = var.node_type
  port                 = 6379
  num_cache_nodes      = var.num_cache_nodes
  
  # Network
  subnet_group_name  = aws_elasticache_subnet_group.main.name
  security_group_ids = var.vpc_security_group_ids
  
  # Security
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  auth_token                 = var.auth_token
  
  # Backup
  snapshot_retention_limit = var.snapshot_retention_limit
  snapshot_window          = var.snapshot_window
  maintenance_window       = var.maintenance_window
  
  # Multi-AZ
  multi_az_enabled = var.multi_az_enabled
  
  # Automatic failover
  automatic_failover_enabled = var.automatic_failover_enabled
  
  # Tags
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-redis"
  })
  
  lifecycle {
    ignore_changes = [
      auth_token
    ]
  }
}

# CloudWatch Log Group for ElastiCache
resource "aws_cloudwatch_log_group" "elasticache" {
  name              = "/aws/elasticache/${var.name_prefix}-redis"
  retention_in_days = var.log_retention_days
  
  tags = var.tags
}
