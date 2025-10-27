# ECR module for Notarius

# ECR Repositories
resource "aws_ecr_repository" "main" {
  for_each = { for repo in var.repositories : repo.name => repo }
  
  name                 = each.value.name
  image_tag_mutability = each.value.image_tag_mutability
  
  image_scanning_configuration {
    scan_on_push = each.value.scan_on_push
  }
  
  encryption_configuration {
    encryption_type = "AES256"
  }
  
  tags = merge(var.tags, {
    Name = each.value.name
  })
}

# ECR Repository Policy
resource "aws_ecr_repository_policy" "main" {
  for_each = { for repo in var.repositories : repo.name => repo if repo.policy != null }
  
  repository = aws_ecr_repository.main[each.key].name
  policy     = each.value.policy
}

# ECR Lifecycle Policy
resource "aws_ecr_lifecycle_policy" "main" {
  for_each = { for repo in var.repositories : repo.name => repo if repo.lifecycle_policy != null }
  
  repository = aws_ecr_repository.main[each.key].name
  
  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 10 images"
        selection = {
          tagStatus     = "tagged"
          tagPrefixList = ["v"]
          countType     = "imageCountMoreThan"
          countNumber   = 10
        }
        action = {
          type = "expire"
        }
      },
      {
        rulePriority = 2
        description  = "Delete untagged images older than 1 day"
        selection = {
          tagStatus   = "untagged"
          countType   = "sinceImagePushed"
          countUnit   = "days"
          countNumber = 1
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}
