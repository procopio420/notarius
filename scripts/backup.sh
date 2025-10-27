#!/bin/bash

# Backup script for Notarius services
# Usage: ./backup.sh [environment] [backup-type]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT="staging"
BACKUP_TYPE="full"
RETENTION_DAYS=30
S3_BUCKET=""
BACKUP_DIR="/tmp/notarius-backup"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -e, --environment ENV    Environment to backup (staging|production) [default: staging]"
    echo "  -t, --type TYPE          Backup type (full|database|files|config) [default: full]"
    echo "  -r, --retention DAYS     Retention period in days [default: 30]"
    echo "  -b, --bucket BUCKET      S3 bucket for backup storage"
    echo "  -d, --dir DIRECTORY      Local backup directory [default: /tmp/notarius-backup]"
    echo "  -h, --help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Full backup of staging"
    echo "  $0 -e production -t database          # Database backup of production"
    echo "  $0 -t files -r 7                     # Files backup with 7-day retention"
    echo "  $0 -b my-backup-bucket               # Backup to specific S3 bucket"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -t|--type)
            BACKUP_TYPE="$2"
            shift 2
            ;;
        -r|--retention)
            RETENTION_DAYS="$2"
            shift 2
            ;;
        -b|--bucket)
            S3_BUCKET="$2"
            shift 2
            ;;
        -d|--dir)
            BACKUP_DIR="$2"
            shift 2
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Validate environment
if [[ "$ENVIRONMENT" != "staging" && "$ENVIRONMENT" != "production" ]]; then
    print_error "Invalid environment: $ENVIRONMENT. Must be 'staging' or 'production'"
    exit 1
fi

# Validate backup type
if [[ "$BACKUP_TYPE" != "full" && "$BACKUP_TYPE" != "database" && "$BACKUP_TYPE" != "files" && "$BACKUP_TYPE" != "config" ]]; then
    print_error "Invalid backup type: $BACKUP_TYPE. Must be 'full', 'database', 'files', or 'config'"
    exit 1
fi

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if kubectl is installed
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl is not installed"
        exit 1
    fi
    
    # Check if aws is installed
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is not installed"
        exit 1
    fi
    
    # Check if pg_dump is installed
    if ! command -v pg_dump &> /dev/null; then
        print_error "pg_dump is not installed"
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Function to check connectivity
check_connectivity() {
    print_status "Checking connectivity..."
    
    # Check kubectl connectivity
    if ! kubectl cluster-info &> /dev/null; then
        print_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    # Check AWS connectivity
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "Cannot connect to AWS"
        exit 1
    fi
    
    print_success "Connectivity check passed"
}

# Function to create backup directory
create_backup_directory() {
    print_status "Creating backup directory: $BACKUP_DIR"
    
    mkdir -p "$BACKUP_DIR"
    
    # Create subdirectories
    mkdir -p "$BACKUP_DIR/database"
    mkdir -p "$BACKUP_DIR/files"
    mkdir -p "$BACKUP_DIR/config"
    mkdir -p "$BACKUP_DIR/logs"
    
    print_success "Backup directory created"
}

# Function to backup database
backup_database() {
    print_status "Backing up database..."
    
    # Get database connection details
    local db_host=$(kubectl get secret postgres-secret -o jsonpath='{.data.host}' | base64 -d 2>/dev/null || echo "localhost")
    local db_port=$(kubectl get secret postgres-secret -o jsonpath='{.data.port}' | base64 -d 2>/dev/null || echo "5432")
    local db_name=$(kubectl get secret postgres-secret -o jsonpath='{.data.database}' | base64 -d 2>/dev/null || echo "notarius")
    local db_user=$(kubectl get secret postgres-secret -o jsonpath='{.data.username}' | base64 -d 2>/dev/null || echo "postgres")
    local db_password=$(kubectl get secret postgres-secret -o jsonpath='{.data.password}' | base64 -d 2>/dev/null || echo "password")
    
    # Set PGPASSWORD environment variable
    export PGPASSWORD="$db_password"
    
    # Create database backup
    local backup_file="$BACKUP_DIR/database/notarius_$(date +%Y%m%d_%H%M%S).sql"
    
    pg_dump -h "$db_host" -p "$db_port" -U "$db_user" -d "$db_name" \
        --verbose --clean --no-owner --no-privileges \
        --file="$backup_file"
    
    # Compress backup
    gzip "$backup_file"
    
    print_success "Database backup completed: ${backup_file}.gz"
}

# Function to backup files
backup_files() {
    print_status "Backing up files..."
    
    # Get S3 bucket name
    local s3_bucket_name=$(kubectl get configmap app-config -o jsonpath='{.data.S3_BUCKET_NAME}' 2>/dev/null || echo "")
    
    if [[ -n "$s3_bucket_name" ]]; then
        # Backup S3 files
        local backup_file="$BACKUP_DIR/files/s3_backup_$(date +%Y%m%d_%H%M%S).tar.gz"
        
        aws s3 sync "s3://$s3_bucket_name" "$BACKUP_DIR/files/s3_content/"
        tar -czf "$backup_file" -C "$BACKUP_DIR/files" s3_content/
        rm -rf "$BACKUP_DIR/files/s3_content/"
        
        print_success "S3 files backup completed: $backup_file"
    else
        print_warning "S3 bucket not configured, skipping files backup"
    fi
}

# Function to backup configuration
backup_config() {
    print_status "Backing up configuration..."
    
    # Backup Kubernetes resources
    local backup_file="$BACKUP_DIR/config/k8s_resources_$(date +%Y%m%d_%H%M%S).yaml"
    
    kubectl get all,secrets,configmaps,persistentvolumeclaims -o yaml > "$backup_file"
    
    # Backup Helm releases
    local helm_backup_file="$BACKUP_DIR/config/helm_releases_$(date +%Y%m%d_%H%M%S).yaml"
    
    helm list -a -o yaml > "$helm_backup_file"
    
    print_success "Configuration backup completed: $backup_file, $helm_backup_file"
}

# Function to backup logs
backup_logs() {
    print_status "Backing up logs..."
    
    # Get pod names
    local pods=$(kubectl get pods -o jsonpath='{.items[*].metadata.name}')
    
    for pod in $pods; do
        if [[ "$pod" == *"notarius"* ]]; then
            local log_file="$BACKUP_DIR/logs/${pod}_$(date +%Y%m%d_%H%M%S).log"
            kubectl logs "$pod" > "$log_file"
        fi
    done
    
    print_success "Logs backup completed"
}

# Function to upload to S3
upload_to_s3() {
    if [[ -z "$S3_BUCKET" ]]; then
        print_warning "S3 bucket not specified, skipping upload"
        return 0
    fi
    
    print_status "Uploading backup to S3: $S3_BUCKET"
    
    # Create backup archive
    local backup_archive="$BACKUP_DIR/notarius_backup_${ENVIRONMENT}_$(date +%Y%m%d_%H%M%S).tar.gz"
    tar -czf "$backup_archive" -C "$BACKUP_DIR" .
    
    # Upload to S3
    aws s3 cp "$backup_archive" "s3://$S3_BUCKET/backups/"
    
    print_success "Backup uploaded to S3: $backup_archive"
}

# Function to cleanup old backups
cleanup_old_backups() {
    print_status "Cleaning up old backups (older than $RETENTION_DAYS days)..."
    
    if [[ -n "$S3_BUCKET" ]]; then
        # Clean up S3 backups
        aws s3 ls "s3://$S3_BUCKET/backups/" | while read -r line; do
            local date_str=$(echo "$line" | awk '{print $1" "$2}')
            local file_name=$(echo "$line" | awk '{print $4}')
            
            if [[ -n "$file_name" ]]; then
                local file_date=$(date -d "$date_str" +%s)
                local cutoff_date=$(date -d "$RETENTION_DAYS days ago" +%s)
                
                if [[ $file_date -lt $cutoff_date ]]; then
                    aws s3 rm "s3://$S3_BUCKET/backups/$file_name"
                    print_status "Deleted old backup: $file_name"
                fi
            fi
        done
    fi
    
    print_success "Old backups cleanup completed"
}

# Function to cleanup local files
cleanup_local_files() {
    print_status "Cleaning up local backup files..."
    
    rm -rf "$BACKUP_DIR"
    
    print_success "Local cleanup completed"
}

# Function to verify backup
verify_backup() {
    print_status "Verifying backup..."
    
    local backup_files=$(find "$BACKUP_DIR" -type f | wc -l)
    
    if [[ $backup_files -gt 0 ]]; then
        print_success "Backup verification passed: $backup_files files created"
    else
        print_error "Backup verification failed: No files created"
        exit 1
    fi
}

# Main backup function
main() {
    print_status "Starting backup for $ENVIRONMENT"
    print_status "Backup type: $BACKUP_TYPE"
    print_status "Retention: $RETENTION_DAYS days"
    print_status "S3 bucket: ${S3_BUCKET:-'Not specified'}"
    
    # Set up error handling
    trap cleanup_local_files EXIT
    
    # Run checks
    check_prerequisites
    check_connectivity
    
    # Create backup directory
    create_backup_directory
    
    # Perform backup based on type
    case "$BACKUP_TYPE" in
        "full")
            backup_database
            backup_files
            backup_config
            backup_logs
            ;;
        "database")
            backup_database
            ;;
        "files")
            backup_files
            ;;
        "config")
            backup_config
            ;;
    esac
    
    # Verify backup
    verify_backup
    
    # Upload to S3 if specified
    upload_to_s3
    
    # Cleanup old backups
    cleanup_old_backups
    
    print_success "Backup completed successfully!"
    
    # Show backup summary
    echo ""
    print_status "Backup Summary:"
    echo "  Environment: $ENVIRONMENT"
    echo "  Type: $BACKUP_TYPE"
    echo "  Retention: $RETENTION_DAYS days"
    echo "  S3 bucket: ${S3_BUCKET:-'Not specified'}"
    echo "  Status: Success"
}

# Run main function
main "$@"
