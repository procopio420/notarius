# Outputs for CloudWatch Logs module

output "log_group_names" {
  description = "Names of the CloudWatch log groups"
  value       = { for k, v in aws_cloudwatch_log_group.main : k => v.name }
}

output "log_group_arns" {
  description = "ARNs of the CloudWatch log groups"
  value       = { for k, v in aws_cloudwatch_log_group.main : k => v.arn }
}

output "log_stream_names" {
  description = "Names of the CloudWatch log streams"
  value       = { for k, v in aws_cloudwatch_log_stream.main : k => v.name }
}

output "metric_filter_names" {
  description = "Names of the CloudWatch metric filters"
  value       = { for k, v in aws_cloudwatch_log_metric_filter.main : k => v.name }
}

output "alarm_names" {
  description = "Names of the CloudWatch alarms"
  value       = { for k, v in aws_cloudwatch_metric_alarm.main : k => v.alarm_name }
}

output "alarm_arns" {
  description = "ARNs of the CloudWatch alarms"
  value       = { for k, v in aws_cloudwatch_metric_alarm.main : k => v.arn }
}
