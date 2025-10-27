# RDS module for Notarius

# Random password for database
resource "random_password" "db_password" {
  length  = 16
  special = true
}

# DB Subnet Group
resource "aws_db_subnet_group" "main" {
  name       = "${var.name_prefix}-db-subnet-group"
  subnet_ids = var.subnets
  
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-db-subnet-group"
  })
}

# DB Parameter Group
resource "aws_db_parameter_group" "main" {
  family = "postgres15"
  name   = "${var.name_prefix}-db-parameter-group"
  
  parameter {
    name  = "log_statement"
    value = "all"
  }
  
  parameter {
    name  = "log_min_duration_statement"
    value = "1000"
  }
  
  parameter {
    name  = "log_checkpoints"
    value = "1"
  }
  
  parameter {
    name  = "log_connections"
    value = "1"
  }
  
  parameter {
    name  = "log_disconnections"
    value = "1"
  }
  
  parameter {
    name  = "log_lock_waits"
    value = "1"
  }
  
  tags = var.tags
}

# DB Option Group
resource "aws_db_option_group" "main" {
  name                 = "${var.name_prefix}-db-option-group"
  option_group_description = "Option group for Notarius database"
  engine_name          = "postgres"
  major_engine_version = "15"
  
  tags = var.tags
}

# RDS Instance
resource "aws_db_instance" "main" {
  identifier = "${var.name_prefix}-db"
  
  # Engine
  engine         = "postgres"
  engine_version = "15.4"
  
  # Instance
  instance_class    = var.instance_class
  allocated_storage = var.allocated_storage
  max_allocated_storage = var.max_allocated_storage
  storage_type      = "gp3"
  storage_encrypted = true
  kms_key_id        = var.kms_key_id
  
  # Database
  db_name  = var.db_name
  username = var.db_username
  password = var.db_password
  
  # Network
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = var.vpc_security_group_ids
  publicly_accessible    = false
  
  # Backup
  backup_retention_period = var.backup_retention_period
  backup_window          = var.backup_window
  maintenance_window     = var.maintenance_window
  delete_automated_backups = false
  
  # Monitoring
  monitoring_interval = var.monitoring_interval
  monitoring_role_arn = var.monitoring_role_arn
  performance_insights_enabled = var.performance_insights_enabled
  performance_insights_retention_period = var.performance_insights_retention_period
  
  # Parameter and Option Groups
  parameter_group_name = aws_db_parameter_group.main.name
  option_group_name    = aws_db_option_group.main.name
  
  # Multi-AZ
  multi_az = var.multi_az
  
  # Deletion protection
  deletion_protection = var.deletion_protection
  skip_final_snapshot = var.skip_final_snapshot
  final_snapshot_identifier = var.skip_final_snapshot ? null : "${var.name_prefix}-final-snapshot-${formatdate("YYYY-MM-DD-hhmm", timestamp())}"
  
  # Tags
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-db"
  })
  
  lifecycle {
    ignore_changes = [
      password,
      final_snapshot_identifier
    ]
  }
}

# DB Instance Automated Backup
resource "aws_db_instance_automated_backups_replication" "main" {
  count = var.enable_cross_region_backup ? 1 : 0
  
  source_db_instance_arn = aws_db_instance.main.arn
  kms_key_id            = var.backup_kms_key_id
  pre_signed_url        = var.backup_pre_signed_url
  retention_period      = var.backup_retention_period
  source_region         = var.source_region
}

# CloudWatch Log Group for RDS
resource "aws_cloudwatch_log_group" "rds" {
  name              = "/aws/rds/instance/${aws_db_instance.main.identifier}/postgresql"
  retention_in_days = var.log_retention_days
  
  tags = var.tags
}

# CloudWatch Log Stream for RDS
resource "aws_cloudwatch_log_stream" "rds" {
  name           = "postgresql"
  log_group_name = aws_cloudwatch_log_group.rds.name
}
