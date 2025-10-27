# CloudWatch Logs module for Notarius

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "main" {
  for_each = { for log_group in var.log_groups : log_group.name => log_group }
  
  name              = each.value.name
  retention_in_days = each.value.retention_in_days
  kms_key_id        = var.kms_key_id
  
  tags = merge(var.tags, {
    Name = each.value.name
  })
}

# CloudWatch Log Streams
resource "aws_cloudwatch_log_stream" "main" {
  for_each = { for log_group in var.log_groups : log_group.name => log_group if log_group.streams != null }
  
  name           = each.value.streams.name
  log_group_name = aws_cloudwatch_log_group.main[each.key].name
}

# CloudWatch Log Metric Filters
resource "aws_cloudwatch_log_metric_filter" "main" {
  for_each = { for log_group in var.log_groups : log_group.name => log_group if log_group.metric_filters != null }
  
  name           = "${each.value.name}-metric-filter"
  log_group_name = aws_cloudwatch_log_group.main[each.key].name
  pattern        = each.value.metric_filters.pattern
  
  metric_transformation {
    name      = each.value.metric_filters.metric_name
    namespace = each.value.metric_filters.namespace
    value     = each.value.metric_filters.value
  }
}

# CloudWatch Alarms
resource "aws_cloudwatch_metric_alarm" "main" {
  for_each = { for log_group in var.log_groups : log_group.name => log_group if log_group.alarms != null }
  
  alarm_name          = "${each.value.name}-alarm"
  comparison_operator = each.value.alarms.comparison_operator
  evaluation_periods  = each.value.alarms.evaluation_periods
  metric_name         = each.value.alarms.metric_name
  namespace           = each.value.alarms.namespace
  period              = each.value.alarms.period
  statistic           = each.value.alarms.statistic
  threshold           = each.value.alarms.threshold
  alarm_description   = each.value.alarms.description
  alarm_actions       = each.value.alarms.alarm_actions
  ok_actions          = each.value.alarms.ok_actions
  treat_missing_data  = each.value.alarms.treat_missing_data
  
  tags = var.tags
}
