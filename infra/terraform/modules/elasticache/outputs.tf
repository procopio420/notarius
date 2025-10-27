# Outputs for ElastiCache module

output "replication_group_id" {
  description = "ID of the ElastiCache replication group"
  value       = aws_elasticache_replication_group.main.id
}

output "replication_group_arn" {
  description = "ARN of the ElastiCache replication group"
  value       = aws_elasticache_replication_group.main.arn
}

output "redis_endpoint" {
  description = "Endpoint of the Redis cluster"
  value       = aws_elasticache_replication_group.main.primary_endpoint_address
}

output "redis_port" {
  description = "Port of the Redis cluster"
  value       = aws_elasticache_replication_group.main.port
}

output "redis_reader_endpoint" {
  description = "Reader endpoint of the Redis cluster"
  value       = aws_elasticache_replication_group.main.reader_endpoint_address
}

output "subnet_group_id" {
  description = "ID of the ElastiCache subnet group"
  value       = aws_elasticache_subnet_group.main.id
}

output "subnet_group_arn" {
  description = "ARN of the ElastiCache subnet group"
  value       = aws_elasticache_subnet_group.main.arn
}

output "parameter_group_id" {
  description = "ID of the ElastiCache parameter group"
  value       = aws_elasticache_parameter_group.main.id
}

output "parameter_group_arn" {
  description = "ARN of the ElastiCache parameter group"
  value       = aws_elasticache_parameter_group.main.arn
}

output "cloudwatch_log_group_name" {
  description = "Name of the CloudWatch log group"
  value       = aws_cloudwatch_log_group.elasticache.name
}

output "cloudwatch_log_group_arn" {
  description = "ARN of the CloudWatch log group"
  value       = aws_cloudwatch_log_group.elasticache.arn
}
