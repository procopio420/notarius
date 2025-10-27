# Variables for KMS module

variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
}

variable "description" {
  description = "Description for the KMS key"
  type        = string
  default     = "KMS key for Notarius encryption"
}

variable "deletion_window_in_days" {
  description = "Deletion window in days"
  type        = number
  default     = 7
}

variable "enable_key_rotation" {
  description = "Enable key rotation"
  type        = bool
  default     = true
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
