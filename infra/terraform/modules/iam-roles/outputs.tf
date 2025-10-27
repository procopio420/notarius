# Outputs for IAM Roles module

output "ecs_task_role_arn" {
  description = "ARN of the ECS task role"
  value       = aws_iam_role.ecs_task_role.arn
}

output "ecs_task_role_name" {
  description = "Name of the ECS task role"
  value       = aws_iam_role.ecs_task_role.name
}

output "ecs_execution_role_arn" {
  description = "ARN of the ECS execution role"
  value       = aws_iam_role.ecs_execution_role.arn
}

output "ecs_execution_role_name" {
  description = "Name of the ECS execution role"
  value       = aws_iam_role.ecs_execution_role.name
}

output "rds_enhanced_monitoring_role_arn" {
  description = "ARN of the RDS enhanced monitoring role"
  value       = var.enable_rds_enhanced_monitoring ? aws_iam_role.rds_enhanced_monitoring_role[0].arn : null
}

output "rds_enhanced_monitoring_role_name" {
  description = "Name of the RDS enhanced monitoring role"
  value       = var.enable_rds_enhanced_monitoring ? aws_iam_role.rds_enhanced_monitoring_role[0].name : null
}

output "lambda_execution_role_arn" {
  description = "ARN of the Lambda execution role"
  value       = var.enable_lambda_execution_role ? aws_iam_role.lambda_execution_role[0].arn : null
}

output "lambda_execution_role_name" {
  description = "Name of the Lambda execution role"
  value       = var.enable_lambda_execution_role ? aws_iam_role.lambda_execution_role[0].name : null
}
