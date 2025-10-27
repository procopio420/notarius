# S3 module for Notarius

# S3 Bucket
resource "aws_s3_bucket" "main" {
  bucket = var.bucket_name
  
  tags = var.tags
}

# S3 Bucket Versioning
resource "aws_s3_bucket_versioning" "main" {
  bucket = aws_s3_bucket.main.id
  versioning_configuration {
    status = var.versioning_enabled ? "Enabled" : "Suspended"
  }
}

# S3 Bucket Encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "main" {
  bucket = aws_s3_bucket.main.id
  
  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = var.encryption_enabled ? var.kms_key_id : null
      sse_algorithm     = var.encryption_enabled ? "aws:kms" : "AES256"
    }
    bucket_key_enabled = var.encryption_enabled
  }
}

# S3 Bucket Public Access Block
resource "aws_s3_bucket_public_access_block" "main" {
  bucket = aws_s3_bucket.main.id
  
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# S3 Bucket Lifecycle Configuration
resource "aws_s3_bucket_lifecycle_configuration" "main" {
  bucket = aws_s3_bucket.main.id
  
  dynamic "rule" {
    for_each = var.lifecycle_rules
    content {
      id     = rule.value.id
      status = rule.value.enabled ? "Enabled" : "Disabled"
      
      dynamic "noncurrent_version_expiration" {
        for_each = rule.value.noncurrent_version_expiration != null ? [rule.value.noncurrent_version_expiration] : []
        content {
          noncurrent_days = noncurrent_version_expiration.value.days
        }
      }
      
      dynamic "abort_incomplete_multipart_upload" {
        for_each = rule.value.abort_incomplete_multipart_upload != null ? [rule.value.abort_incomplete_multipart_upload] : []
        content {
          days_after_initiation = abort_incomplete_multipart_upload.value.days_after_initiation
        }
      }
    }
  }
}

# S3 Bucket Notification
resource "aws_s3_bucket_notification" "main" {
  bucket = aws_s3_bucket.main.id
  
  dynamic "lambda_function" {
    for_each = var.lambda_notifications
    content {
      lambda_function_arn = lambda_function.value.function_arn
      events              = lambda_function.value.events
      filter_prefix       = lambda_function.value.filter_prefix
      filter_suffix       = lambda_function.value.filter_suffix
    }
  }
  
  dynamic "queue" {
    for_each = var.sqs_notifications
    content {
      queue_arn     = queue.value.queue_arn
      events        = queue.value.events
      filter_prefix = queue.value.filter_prefix
      filter_suffix = queue.value.filter_suffix
    }
  }
}

# S3 Bucket Policy
resource "aws_s3_bucket_policy" "main" {
  bucket = aws_s3_bucket.main.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "DenyInsecureConnections"
        Effect    = "Deny"
        Principal = "*"
        Action    = "s3:*"
        Resource = [
          aws_s3_bucket.main.arn,
          "${aws_s3_bucket.main.arn}/*"
        ]
        Condition = {
          Bool = {
            "aws:SecureTransport" = "false"
          }
        }
      }
    ]
  })
}

# S3 Bucket CORS Configuration
resource "aws_s3_bucket_cors_configuration" "main" {
  bucket = aws_s3_bucket.main.id
  
  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "PUT", "POST", "DELETE", "HEAD"]
    allowed_origins = var.cors_allowed_origins
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }
}

# S3 Bucket Logging
resource "aws_s3_bucket_logging" "main" {
  count = var.logging_enabled ? 1 : 0
  
  bucket = aws_s3_bucket.main.id
  
  target_bucket = var.logging_target_bucket
  target_prefix = var.logging_target_prefix
}

# S3 Bucket Replication
resource "aws_s3_bucket_replication_configuration" "main" {
  count = var.replication_enabled ? 1 : 0
  
  bucket = aws_s3_bucket.main.id
  role   = var.replication_role_arn
  
  rule {
    id     = "replication-rule"
    status = "Enabled"
    
    destination {
      bucket        = var.replication_destination_bucket
      storage_class = var.replication_storage_class
      
      dynamic "encryption_configuration" {
        for_each = var.replication_encryption_configuration != null ? [var.replication_encryption_configuration] : []
        content {
          replica_kms_key_id = encryption_configuration.value.replica_kms_key_id
        }
      }
    }
  }
}
