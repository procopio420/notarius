# Variables for ECR module

variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
}

variable "repositories" {
  description = "List of ECR repositories to create"
  type = list(object({
    name                 = string
    image_tag_mutability = string
    scan_on_push         = bool
    policy               = optional(string)
    lifecycle_policy     = optional(string)
  }))
  default = []
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
