# IAM Roles module for Notarius

# ECS Task Role
resource "aws_iam_role" "ecs_task_role" {
  name = "${var.name_prefix}-ecs-task-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
  
  tags = var.tags
}

# ECS Execution Role
resource "aws_iam_role" "ecs_execution_role" {
  name = "${var.name_prefix}-ecs-execution-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
  
  tags = var.tags
}

# ECS Task Role Policies
resource "aws_iam_role_policy" "ecs_task_role_policy" {
  for_each = { for policy in var.ecs_task_role_policies : policy.name => policy }
  
  name = "${var.name_prefix}-ecs-task-role-${each.key}"
  role = aws_iam_role.ecs_task_role.id
  
  policy = each.value.policy
}

# ECS Execution Role Policy Attachment
resource "aws_iam_role_policy_attachment" "ecs_execution_role_policy" {
  role       = aws_iam_role.ecs_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# ECS Execution Role Policies
resource "aws_iam_role_policy" "ecs_execution_role_policy" {
  for_each = { for policy in var.ecs_execution_role_policies : policy.name => policy }
  
  name = "${var.name_prefix}-ecs-execution-role-${each.key}"
  role = aws_iam_role.ecs_execution_role.id
  
  policy = each.value.policy
}

# RDS Enhanced Monitoring Role
resource "aws_iam_role" "rds_enhanced_monitoring_role" {
  count = var.enable_rds_enhanced_monitoring ? 1 : 0
  
  name = "${var.name_prefix}-rds-enhanced-monitoring-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "monitoring.rds.amazonaws.com"
        }
      }
    ]
  })
  
  tags = var.tags
}

# RDS Enhanced Monitoring Role Policy Attachment
resource "aws_iam_role_policy_attachment" "rds_enhanced_monitoring_role_policy" {
  count = var.enable_rds_enhanced_monitoring ? 1 : 0
  
  role       = aws_iam_role.rds_enhanced_monitoring_role[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}

# Lambda Execution Role
resource "aws_iam_role" "lambda_execution_role" {
  count = var.enable_lambda_execution_role ? 1 : 0
  
  name = "${var.name_prefix}-lambda-execution-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
  
  tags = var.tags
}

# Lambda Execution Role Policy Attachment
resource "aws_iam_role_policy_attachment" "lambda_execution_role_policy" {
  count = var.enable_lambda_execution_role ? 1 : 0
  
  role       = aws_iam_role.lambda_execution_role[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Lambda Execution Role Policies
resource "aws_iam_role_policy" "lambda_execution_role_policy" {
  for_each = var.enable_lambda_execution_role ? { for policy in var.lambda_execution_role_policies : policy.name => policy } : {}
  
  name = "${var.name_prefix}-lambda-execution-role-${each.key}"
  role = aws_iam_role.lambda_execution_role[0].id
  
  policy = each.value.policy
}
