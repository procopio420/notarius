# Variables for S3 module

variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
}

variable "bucket_name" {
  description = "Name of the S3 bucket"
  type        = string
}

variable "versioning_enabled" {
  description = "Enable versioning"
  type        = bool
  default     = true
}

variable "encryption_enabled" {
  description = "Enable encryption"
  type        = bool
  default     = true
}

variable "kms_key_id" {
  description = "KMS key ID for encryption"
  type        = string
  default     = null
}

variable "lifecycle_rules" {
  description = "Lifecycle rules for the bucket"
  type = list(object({
    id      = string
    enabled = bool
    noncurrent_version_expiration = optional(object({
      days = number
    }))
    abort_incomplete_multipart_upload = optional(object({
      days_after_initiation = number
    }))
  }))
  default = []
}

variable "lambda_notifications" {
  description = "Lambda function notifications"
  type = list(object({
    function_arn = string
    events       = list(string)
    filter_prefix = optional(string)
    filter_suffix = optional(string)
  }))
  default = []
}

variable "sqs_notifications" {
  description = "SQS queue notifications"
  type = list(object({
    queue_arn     = string
    events        = list(string)
    filter_prefix = optional(string)
    filter_suffix = optional(string)
  }))
  default = []
}

variable "cors_allowed_origins" {
  description = "CORS allowed origins"
  type        = list(string)
  default     = []
}

variable "logging_enabled" {
  description = "Enable logging"
  type        = bool
  default     = false
}

variable "logging_target_bucket" {
  description = "Target bucket for logging"
  type        = string
  default     = null
}

variable "logging_target_prefix" {
  description = "Target prefix for logging"
  type        = string
  default     = null
}

variable "replication_enabled" {
  description = "Enable replication"
  type        = bool
  default     = false
}

variable "replication_role_arn" {
  description = "ARN of the replication role"
  type        = string
  default     = null
}

variable "replication_destination_bucket" {
  description = "Destination bucket for replication"
  type        = string
  default     = null
}

variable "replication_storage_class" {
  description = "Storage class for replication"
  type        = string
  default     = "STANDARD"
}

variable "replication_encryption_configuration" {
  description = "Encryption configuration for replication"
  type = object({
    replica_kms_key_id = string
  })
  default = null
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
