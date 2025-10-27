# Secrets Manager module for Notarius

# Random password for secrets
resource "random_password" "secrets" {
  for_each = var.secrets
  
  length  = 32
  special = true
}

# Secrets Manager Secret
resource "aws_secretsmanager_secret" "main" {
  name                    = "${var.name_prefix}-secrets"
  description             = "Secrets for Notarius application"
  recovery_window_in_days = var.recovery_window_in_days
  
  tags = var.tags
}

# Secrets Manager Secret Version
resource "aws_secretsmanager_secret_version" "main" {
  secret_id = aws_secretsmanager_secret.main.id
  secret_string = jsonencode({
    for key, value in var.secrets : key => value
  })
}

# Secrets Manager Secret Policy
resource "aws_secretsmanager_secret_policy" "main" {
  secret_arn = aws_secretsmanager_secret.main.arn
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "secretsmanager:*"
        Resource = "*"
      },
      {
        Sid    = "Allow ECS Tasks"
        Effect = "Allow"
        Principal = {
          AWS = var.ecs_task_role_arn
        }
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = aws_secretsmanager_secret.main.arn
      }
    ]
  })
}

# Data source for current AWS account
data "aws_caller_identity" "current" {}
