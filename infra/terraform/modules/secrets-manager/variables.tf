# Variables for Secrets Manager module

variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
}

variable "secrets" {
  description = "Secrets to store"
  type        = map(string)
  sensitive   = true
}

variable "recovery_window_in_days" {
  description = "Recovery window in days"
  type        = number
  default     = 7
}

variable "ecs_task_role_arn" {
  description = "ARN of the ECS task role"
  type        = string
  default     = null
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
