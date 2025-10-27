# Notarius Scripts

This directory contains utility scripts for managing the Notarius system.

## Scripts Overview

### 1. Deployment Script (`deploy.sh`)

Automated deployment script for Notarius services.

**Usage:**
```bash
./deploy.sh [OPTIONS]
```

**Options:**
- `-e, --environment ENV`: Environment to deploy to (staging|production) [default: staging]
- `-s, --service SERVICE`: Service to deploy (notarius-api|pii-vault|lexnode-api|intent-engine|all) [default: all]
- `-v, --version VERSION`: Version to deploy [default: latest]
- `-d, --dry-run`: Show what would be deployed without actually deploying
- `-f, --force`: Force deployment even if checks fail
- `-h, --help`: Show help message

**Examples:**
```bash
# Deploy all services to staging
./deploy.sh

# Deploy notarius-api to production
./deploy.sh -e production -s notarius-api

# Dry run deployment of v1.2.3
./deploy.sh -v v1.2.3 -d

# Force deploy to production
./deploy.sh -e production -f
```

**Features:**
- Prerequisites checking
- Environment connectivity validation
- Infrastructure deployment with Terraform
- Service deployment with Helm
- Health checks and smoke tests
- Rollback capabilities
- Comprehensive logging

### 2. Backup Script (`backup.sh`)

Automated backup script for Notarius services.

**Usage:**
```bash
./backup.sh [OPTIONS]
```

**Options:**
- `-e, --environment ENV`: Environment to backup (staging|production) [default: staging]
- `-t, --type TYPE`: Backup type (full|database|files|config) [default: full]
- `-r, --retention DAYS`: Retention period in days [default: 30]
- `-b, --bucket BUCKET`: S3 bucket for backup storage
- `-d, --dir DIRECTORY`: Local backup directory [default: /tmp/notarius-backup]
- `-h, --help`: Show help message

**Examples:**
```bash
# Full backup of staging
./backup.sh

# Database backup of production
./backup.sh -e production -t database

# Files backup with 7-day retention
./backup.sh -t files -r 7

# Backup to specific S3 bucket
./backup.sh -b my-backup-bucket
```

**Features:**
- Database backup with pg_dump
- S3 files backup
- Kubernetes configuration backup
- Log backup
- S3 upload with compression
- Automatic cleanup of old backups
- Backup verification

### 3. Monitoring Script (`monitor.sh`)

Comprehensive monitoring script for Notarius services.

**Usage:**
```bash
./monitor.sh [OPTIONS]
```

**Options:**
- `-e, --environment ENV`: Environment to monitor (staging|production) [default: staging]
- `-t, --type TYPE`: Check type (all|health|performance|logs|alerts) [default: all]
- `-c, --cpu-threshold %`: CPU alert threshold percentage [default: 80]
- `-m, --memory-threshold %`: Memory alert threshold percentage [default: 85]
- `-d, --disk-threshold %`: Disk alert threshold percentage [default: 90]
- `-a, --alert-email EMAIL`: Email for alerts
- `-h, --help`: Show help message

**Examples:**
```bash
# Monitor all aspects of staging
./monitor.sh

# Health check of production
./monitor.sh -e production -t health

# Performance check with custom thresholds
./monitor.sh -t performance -c 70 -m 80

# Check alerts and send email
./monitor.sh -t alerts -a admin@example.com
```

**Features:**
- Service health monitoring
- Performance metrics checking
- Log error analysis
- System alert detection
- Email notifications
- Comprehensive reporting

### 4. Helm Chart Update Script (`update-helm-charts.py`)

Python script to update Helm chart versions.

**Usage:**
```bash
python3 update-helm-charts.py <version>
```

**Examples:**
```bash
# Update all charts to v1.2.3
python3 update-helm-charts.py v1.2.3
```

**Features:**
- Updates Chart.yaml version and appVersion
- Updates values.yaml image tags
- Validates version format
- Provides detailed output
- Handles multiple charts

## Prerequisites

### Common Requirements

All scripts require the following tools to be installed and configured:

- **kubectl**: Kubernetes command-line tool
- **helm**: Helm package manager
- **docker**: Docker container runtime
- **aws**: AWS CLI
- **terraform**: Infrastructure as Code tool

### Environment Setup

1. **Kubernetes Access**: Ensure kubectl is configured to access your cluster
2. **AWS Credentials**: Configure AWS CLI with appropriate credentials
3. **Helm Repositories**: Add required Helm repositories
4. **Docker Registry**: Configure access to container registry

### Service-Specific Requirements

#### Deployment Script
- Terraform state backend configured
- ECR repository access
- Kubernetes cluster access
- Helm charts available

#### Backup Script
- PostgreSQL client tools (pg_dump)
- S3 bucket access
- Kubernetes cluster access
- Local storage for temporary files

#### Monitoring Script
- Kubernetes cluster access
- Metrics server enabled
- Log aggregation configured
- Email server (for alerts)

## Configuration

### Environment Variables

Set the following environment variables for script execution:

```bash
# AWS Configuration
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-east-1"

# Kubernetes Configuration
export KUBECONFIG="path/to/kubeconfig"

# Application Configuration
export NOTARIUS_ENVIRONMENT="staging"
export NOTARIUS_VERSION="latest"
```

### Configuration Files

#### Terraform Variables
Create environment-specific variable files:
- `staging.tfvars`
- `production.tfvars`

#### Helm Values
Create environment-specific values files:
- `staging-values.yaml`
- `production-values.yaml`

## Best Practices

### Security

1. **Credentials**: Store credentials securely, never in scripts
2. **Permissions**: Use least-privilege access principles
3. **Secrets**: Use Kubernetes secrets for sensitive data
4. **Audit**: Enable audit logging for all operations

### Reliability

1. **Backup**: Regular automated backups
2. **Monitoring**: Continuous monitoring and alerting
3. **Testing**: Test scripts in staging before production
4. **Rollback**: Always have rollback procedures

### Maintenance

1. **Updates**: Keep scripts and dependencies updated
2. **Documentation**: Maintain up-to-date documentation
3. **Testing**: Regular testing of scripts
4. **Monitoring**: Monitor script execution and results

## Troubleshooting

### Common Issues

1. **Permission Denied**: Check file permissions and user access
2. **Connection Failed**: Verify network connectivity and credentials
3. **Resource Not Found**: Check resource names and namespaces
4. **Timeout**: Increase timeout values for slow operations

### Debug Mode

Enable debug mode for detailed output:

```bash
# Enable bash debug mode
set -x

# Run script with debug output
./deploy.sh -e staging -s notarius-api
```

### Log Files

Scripts generate log files in:
- `/tmp/notarius-deploy-*`
- `/tmp/notarius-backup-*`
- `/tmp/notarius-monitor-*`

## Automation

### Cron Jobs

Set up automated execution with cron:

```bash
# Daily backup at 2 AM
0 2 * * * /path/to/scripts/backup.sh -e production -t full

# Hourly monitoring
0 * * * * /path/to/scripts/monitor.sh -e production -t health

# Weekly performance check
0 4 * * 0 /path/to/scripts/monitor.sh -e production -t performance
```

### CI/CD Integration

Integrate scripts into CI/CD pipelines:

```yaml
# GitHub Actions example
- name: Deploy to Staging
  run: |
    ./scripts/deploy.sh -e staging -s all

- name: Run Health Checks
  run: |
    ./scripts/monitor.sh -e staging -t health
```

## Support

### Getting Help

1. Check script help: `./script.sh -h`
2. Review logs and error messages
3. Consult documentation
4. Contact the development team

### Contributing

1. Follow coding standards
2. Add comprehensive error handling
3. Include help documentation
4. Test thoroughly
5. Update this README

## License

These scripts are part of the Notarius project and follow the same licensing terms.
