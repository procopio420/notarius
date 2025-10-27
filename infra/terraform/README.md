# Notarius Terraform Infrastructure

This directory contains Terraform configurations for deploying the Notarius system to AWS.

## Overview

The infrastructure is designed to be production-ready with the following components:

- **VPC**: Isolated network environment with public and private subnets
- **ECS**: Container orchestration for microservices
- **RDS**: PostgreSQL database with Multi-AZ deployment
- **ElastiCache**: Redis for caching and session storage
- **S3**: Object storage for documents and assets
- **KMS**: Encryption key management
- **Secrets Manager**: Secure storage of sensitive configuration
- **CloudWatch**: Logging and monitoring
- **ECR**: Container image registry
- **IAM**: Role-based access control

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                           Internet                              │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│                    ALB (Load Balancer)                         │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│                    ECS Cluster                                  │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│
│  │ Notarius API│ │  PII Vault  │ │ LexNode API │ │Intent Engine││
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘│
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│                    RDS (PostgreSQL)                            │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    ElastiCache (Redis)                         │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    S3 (Document Storage)                       │
└─────────────────────────────────────────────────────────────────┘
```

## Prerequisites

1. **AWS CLI** configured with appropriate credentials
2. **Terraform** >= 1.0 installed
3. **AWS Account** with sufficient permissions
4. **Domain name** (optional, for SSL certificate)

## Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd notarius/infra/terraform
```

### 2. Configure Variables

```bash
# Copy the example variables file
cp terraform.tfvars.example terraform.tfvars

# Edit the variables file with your values
nano terraform.tfvars
```

### 3. Initialize Terraform

```bash
terraform init
```

### 4. Plan Deployment

```bash
terraform plan
```

### 5. Deploy Infrastructure

```bash
terraform apply
```

## Configuration

### Required Variables

- `aws_region`: AWS region for deployment
- `aws_account_id`: Your AWS account ID
- `db_password`: Database password
- `secret_key`: Django secret key

### Optional Variables

- `ssl_certificate_arn`: ARN of SSL certificate for HTTPS
- `domain_name`: Domain name for the application
- `monitoring_email`: Email for monitoring alerts

### Environment-Specific Configuration

The infrastructure supports multiple environments:

- **Development**: Minimal resources, single AZ
- **Staging**: Production-like setup with reduced capacity
- **Production**: Full Multi-AZ deployment with monitoring

## Modules

### Core Infrastructure

- **VPC**: Network isolation and security
- **Security Groups**: Firewall rules
- **ALB**: Load balancing and SSL termination

### Compute

- **ECS Cluster**: Container orchestration
- **ECS Service**: Service definition and scaling
- **ECS Task Definition**: Container configuration

### Data Storage

- **RDS**: PostgreSQL database
- **ElastiCache**: Redis cache
- **S3**: Object storage

### Security

- **KMS**: Encryption key management
- **Secrets Manager**: Secure configuration storage
- **IAM**: Access control

### Monitoring

- **CloudWatch**: Logging and metrics
- **ECR**: Container registry

## Security Features

### Network Security

- VPC with public and private subnets
- Security groups with least-privilege access
- NAT Gateway for outbound internet access
- VPC Endpoints for AWS services

### Data Protection

- Encryption at rest for all data stores
- Encryption in transit for all communications
- KMS key management
- Secrets Manager for sensitive data

### Access Control

- IAM roles with minimal permissions
- ECS task roles for service access
- RDS enhanced monitoring
- CloudWatch logging

## Monitoring and Observability

### CloudWatch Integration

- Application logs
- System metrics
- Custom metrics
- Alarms and notifications

### Log Management

- Centralized logging
- Log retention policies
- Log analysis and alerting
- Compliance logging

### Performance Monitoring

- RDS Performance Insights
- ECS service metrics
- ALB access logs
- Custom application metrics

## Backup and Disaster Recovery

### Automated Backups

- RDS automated backups
- S3 versioning
- Cross-region replication (optional)
- Point-in-time recovery

### Disaster Recovery

- Multi-AZ deployment
- Cross-region backup
- Infrastructure as Code
- Automated failover

## Cost Optimization

### Resource Sizing

- Right-sized instances
- Auto-scaling policies
- Spot instances (optional)
- Reserved instances (optional)

### Storage Optimization

- S3 lifecycle policies
- ECR image cleanup
- Log retention policies
- Backup retention

## Deployment Strategies

### Blue-Green Deployment

1. Deploy new version to separate environment
2. Test and validate
3. Switch traffic to new version
4. Decommission old version

### Rolling Deployment

1. Update ECS service
2. Gradual replacement of tasks
3. Health checks and rollback
4. Zero-downtime deployment

## Maintenance

### Regular Tasks

- Security updates
- Performance monitoring
- Cost optimization
- Backup verification

### Scaling

- Horizontal scaling via ECS
- Database scaling via RDS
- Cache scaling via ElastiCache
- Storage scaling via S3

## Troubleshooting

### Common Issues

1. **Service Unavailable**: Check ECS service status
2. **Database Connection**: Verify security groups
3. **SSL Certificate**: Check certificate validity
4. **Performance**: Monitor CloudWatch metrics

### Debug Commands

```bash
# Check ECS service status
aws ecs describe-services --cluster <cluster-name> --services <service-name>

# Check RDS instance status
aws rds describe-db-instances --db-instance-identifier <instance-id>

# Check CloudWatch logs
aws logs describe-log-groups --log-group-name-prefix /aws/ecs/
```

## Best Practices

### Infrastructure

- Use Infrastructure as Code
- Implement proper tagging
- Follow security best practices
- Monitor and alert

### Application

- Use health checks
- Implement graceful shutdown
- Log appropriately
- Handle errors gracefully

### Operations

- Regular backups
- Security updates
- Performance monitoring
- Cost optimization

## Contributing

### Adding New Resources

1. Create new module in `modules/` directory
2. Add variables and outputs
3. Update main configuration
4. Test with `terraform plan`

### Modifying Existing Resources

1. Update module configuration
2. Test changes with `terraform plan`
3. Apply changes with `terraform apply`
4. Verify functionality

## Support

For issues and questions:

1. Check CloudWatch logs
2. Review Terraform state
3. Consult AWS documentation
4. Contact the development team

## License

This infrastructure code is part of the Notarius project and follows the same licensing terms.
