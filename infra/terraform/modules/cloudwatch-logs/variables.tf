# Variables for CloudWatch Logs module

variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
}

variable "log_groups" {
  description = "List of log groups to create"
  type = list(object({
    name              = string
    retention_in_days = number
    streams = optional(object({
      name = string
    }))
    metric_filters = optional(object({
      pattern     = string
      metric_name = string
      namespace   = string
      value       = string
    }))
    alarms = optional(object({
      comparison_operator = string
      evaluation_periods  = number
      metric_name         = string
      namespace           = string
      period              = number
      statistic           = string
      threshold           = number
      description         = string
      alarm_actions       = list(string)
      ok_actions          = list(string)
      treat_missing_data  = string
    }))
  }))
  default = []
}

variable "kms_key_id" {
  description = "KMS key ID for encryption"
  type        = string
  default     = null
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
