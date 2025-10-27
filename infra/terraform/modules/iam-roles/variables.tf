# Variables for IAM Roles module

variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
}

variable "ecs_task_role_policies" {
  description = "List of policies for ECS task role"
  type = list(object({
    name   = string
    policy = string
  }))
  default = []
}

variable "ecs_execution_role_policies" {
  description = "List of policies for ECS execution role"
  type = list(object({
    name   = string
    policy = string
  }))
  default = []
}

variable "enable_rds_enhanced_monitoring" {
  description = "Enable RDS enhanced monitoring role"
  type        = bool
  default     = false
}

variable "enable_lambda_execution_role" {
  description = "Enable Lambda execution role"
  type        = bool
  default     = false
}

variable "lambda_execution_role_policies" {
  description = "List of policies for Lambda execution role"
  type = list(object({
    name   = string
    policy = string
  }))
  default = []
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
