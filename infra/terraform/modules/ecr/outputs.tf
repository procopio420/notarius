# Outputs for ECR module

output "repository_names" {
  description = "Names of the ECR repositories"
  value       = { for k, v in aws_ecr_repository.main : k => v.name }
}

output "repository_arns" {
  description = "ARNs of the ECR repositories"
  value       = { for k, v in aws_ecr_repository.main : k => v.arn }
}

output "repository_urls" {
  description = "URLs of the ECR repositories"
  value       = { for k, v in aws_ecr_repository.main : k => v.repository_url }
}

output "registry_id" {
  description = "Registry ID of the ECR repositories"
  value       = { for k, v in aws_ecr_repository.main : k => v.registry_id }
}
