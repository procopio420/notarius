# Outputs for Secrets Manager module

output "secret_id" {
  description = "ID of the Secrets Manager secret"
  value       = aws_secretsmanager_secret.main.id
}

output "secret_arn" {
  description = "ARN of the Secrets Manager secret"
  value       = aws_secretsmanager_secret.main.arn
}

output "secret_name" {
  description = "Name of the Secrets Manager secret"
  value       = aws_secretsmanager_secret.main.name
}

output "secret_version_id" {
  description = "Version ID of the Secrets Manager secret"
  value       = aws_secretsmanager_secret_version.main.version_id
}
