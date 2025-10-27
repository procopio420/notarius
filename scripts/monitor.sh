#!/bin/bash

# Monitoring script for Notarius services
# Usage: ./monitor.sh [environment] [check-type]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT="staging"
CHECK_TYPE="all"
ALERT_THRESHOLD_CPU=80
ALERT_THRESHOLD_MEMORY=85
ALERT_THRESHOLD_DISK=90
ALERT_EMAIL=""

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
    echo "  -e, --environment ENV    Environment to monitor (staging|production) [default: staging]"
    echo "  -t, --type TYPE          Check type (all|health|performance|logs|alerts) [default: all]"
    echo "  -c, --cpu-threshold %    CPU alert threshold percentage [default: 80]"
    echo "  -m, --memory-threshold % Memory alert threshold percentage [default: 85]"
    echo "  -d, --disk-threshold %   Disk alert threshold percentage [default: 90]"
    echo "  -a, --alert-email EMAIL  Email for alerts"
    echo "  -h, --help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Monitor all aspects of staging"
    echo "  $0 -e production -t health            # Health check of production"
    echo "  $0 -t performance -c 70 -m 80         # Performance check with custom thresholds"
    echo "  $0 -t alerts -a admin@example.com     # Check alerts and send email"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -t|--type)
            CHECK_TYPE="$2"
            shift 2
            ;;
        -c|--cpu-threshold)
            ALERT_THRESHOLD_CPU="$2"
            shift 2
            ;;
        -m|--memory-threshold)
            ALERT_THRESHOLD_MEMORY="$2"
            shift 2
            ;;
        -d|--disk-threshold)
            ALERT_THRESHOLD_DISK="$2"
            shift 2
            ;;
        -a|--alert-email)
            ALERT_EMAIL="$2"
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

# Validate check type
if [[ "$CHECK_TYPE" != "all" && "$CHECK_TYPE" != "health" && "$CHECK_TYPE" != "performance" && "$CHECK_TYPE" != "logs" && "$CHECK_TYPE" != "alerts" ]]; then
    print_error "Invalid check type: $CHECK_TYPE. Must be 'all', 'health', 'performance', 'logs', or 'alerts'"
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
    
    # Check if helm is installed
    if ! command -v helm &> /dev/null; then
        print_error "Helm is not installed"
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
    
    print_success "Connectivity check passed"
}

# Function to check service health
check_service_health() {
    print_status "Checking service health..."
    
    local services=("notarius-api" "pii-vault" "lexnode-api" "intent-engine")
    local healthy_services=()
    local unhealthy_services=()
    
    for service in "${services[@]}"; do
        # Check if service exists
        if kubectl get service "$service" &> /dev/null; then
            # Check pod status
            local pod_status=$(kubectl get pods -l app="$service" -o jsonpath='{.items[0].status.phase}' 2>/dev/null || echo "NotFound")
            
            if [[ "$pod_status" == "Running" ]]; then
                healthy_services+=("$service")
                print_success "$service is healthy"
            else
                unhealthy_services+=("$service")
                print_error "$service is unhealthy (status: $pod_status)"
            fi
        else
            unhealthy_services+=("$service")
            print_error "$service is not deployed"
        fi
    done
    
    # Summary
    echo ""
    print_status "Health Check Summary:"
    echo "  Healthy services: ${#healthy_services[@]}"
    echo "  Unhealthy services: ${#unhealthy_services[@]}"
    
    if [[ ${#unhealthy_services[@]} -gt 0 ]]; then
        echo "  Unhealthy services: ${unhealthy_services[*]}"
        return 1
    fi
    
    return 0
}

# Function to check performance metrics
check_performance() {
    print_status "Checking performance metrics..."
    
    local services=("notarius-api" "pii-vault" "lexnode-api" "intent-engine")
    local alerts=()
    
    for service in "${services[@]}"; do
        # Check if service exists
        if kubectl get service "$service" &> /dev/null; then
            # Get pod name
            local pod_name=$(kubectl get pods -l app="$service" -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
            
            if [[ -n "$pod_name" ]]; then
                # Get CPU usage
                local cpu_usage=$(kubectl top pod "$pod_name" --no-headers 2>/dev/null | awk '{print $2}' | sed 's/%//' || echo "0")
                
                # Get memory usage
                local memory_usage=$(kubectl top pod "$pod_name" --no-headers 2>/dev/null | awk '{print $3}' | sed 's/%//' || echo "0")
                
                # Check thresholds
                if [[ $cpu_usage -gt $ALERT_THRESHOLD_CPU ]]; then
                    alerts+=("$service: CPU usage ${cpu_usage}% (threshold: ${ALERT_THRESHOLD_CPU}%)")
                fi
                
                if [[ $memory_usage -gt $ALERT_THRESHOLD_MEMORY ]]; then
                    alerts+=("$service: Memory usage ${memory_usage}% (threshold: ${ALERT_THRESHOLD_MEMORY}%)")
                fi
                
                print_status "$service - CPU: ${cpu_usage}%, Memory: ${memory_usage}%"
            fi
        fi
    done
    
    # Check disk usage
    local disk_usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    if [[ $disk_usage -gt $ALERT_THRESHOLD_DISK ]]; then
        alerts+=("System: Disk usage ${disk_usage}% (threshold: ${ALERT_THRESHOLD_DISK}%)")
    fi
    
    # Summary
    echo ""
    print_status "Performance Check Summary:"
    echo "  CPU threshold: ${ALERT_THRESHOLD_CPU}%"
    echo "  Memory threshold: ${ALERT_THRESHOLD_MEMORY}%"
    echo "  Disk threshold: ${ALERT_THRESHOLD_DISK}%"
    echo "  Alerts: ${#alerts[@]}"
    
    if [[ ${#alerts[@]} -gt 0 ]]; then
        echo "  Alert details:"
        for alert in "${alerts[@]}"; do
            print_warning "    $alert"
        done
        return 1
    fi
    
    return 0
}

# Function to check logs
check_logs() {
    print_status "Checking logs for errors..."
    
    local services=("notarius-api" "pii-vault" "lexnode-api" "intent-engine")
    local error_count=0
    
    for service in "${services[@]}"; do
        # Get pod name
        local pod_name=$(kubectl get pods -l app="$service" -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
        
        if [[ -n "$pod_name" ]]; then
            # Check for errors in logs
            local errors=$(kubectl logs "$pod_name" --tail=100 2>/dev/null | grep -i "error\|exception\|fatal\|critical" | wc -l)
            
            if [[ $errors -gt 0 ]]; then
                print_warning "$service has $errors errors in recent logs"
                error_count=$((error_count + errors))
            else
                print_success "$service logs are clean"
            fi
        fi
    done
    
    # Summary
    echo ""
    print_status "Log Check Summary:"
    echo "  Total errors found: $error_count"
    
    if [[ $error_count -gt 0 ]]; then
        return 1
    fi
    
    return 0
}

# Function to check alerts
check_alerts() {
    print_status "Checking system alerts..."
    
    local alerts=()
    
    # Check for failed pods
    local failed_pods=$(kubectl get pods --field-selector=status.phase=Failed -o jsonpath='{.items[*].metadata.name}' 2>/dev/null)
    if [[ -n "$failed_pods" ]]; then
        alerts+=("Failed pods: $failed_pods")
    fi
    
    # Check for pending pods
    local pending_pods=$(kubectl get pods --field-selector=status.phase=Pending -o jsonpath='{.items[*].metadata.name}' 2>/dev/null)
    if [[ -n "$pending_pods" ]]; then
        alerts+=("Pending pods: $pending_pods")
    fi
    
    # Check for restarted pods
    local restarted_pods=$(kubectl get pods -o jsonpath='{.items[?(@.status.containerStatuses[0].restartCount>0)].metadata.name}' 2>/dev/null)
    if [[ -n "$restarted_pods" ]]; then
        alerts+=("Restarted pods: $restarted_pods")
    fi
    
    # Check for resource limits
    local resource_limits=$(kubectl describe nodes | grep -i "resource.*limit" | wc -l)
    if [[ $resource_limits -gt 0 ]]; then
        alerts+=("Resource limits reached on nodes")
    fi
    
    # Summary
    echo ""
    print_status "Alert Check Summary:"
    echo "  Alerts found: ${#alerts[@]}"
    
    if [[ ${#alerts[@]} -gt 0 ]]; then
        echo "  Alert details:"
        for alert in "${alerts[@]}"; do
            print_warning "    $alert"
        done
        
        # Send email alert if configured
        if [[ -n "$ALERT_EMAIL" ]]; then
            send_alert_email "${alerts[@]}"
        fi
        
        return 1
    fi
    
    return 0
}

# Function to send alert email
send_alert_email() {
    local alerts=("$@")
    
    print_status "Sending alert email to $ALERT_EMAIL..."
    
    local subject="Notarius Alert - $ENVIRONMENT Environment"
    local body="The following alerts were detected in the $ENVIRONMENT environment:\n\n"
    
    for alert in "${alerts[@]}"; do
        body+="- $alert\n"
    done
    
    body+="\nPlease investigate these issues immediately.\n\n"
    body+="Generated at: $(date)"
    
    # Send email (requires mail command or similar)
    if command -v mail &> /dev/null; then
        echo -e "$body" | mail -s "$subject" "$ALERT_EMAIL"
        print_success "Alert email sent"
    else
        print_warning "Mail command not available, cannot send email alert"
    fi
}

# Function to generate monitoring report
generate_report() {
    print_status "Generating monitoring report..."
    
    local report_file="/tmp/notarius_monitoring_report_$(date +%Y%m%d_%H%M%S).txt"
    
    {
        echo "Notarius Monitoring Report"
        echo "Generated: $(date)"
        echo "Environment: $ENVIRONMENT"
        echo "Check Type: $CHECK_TYPE"
        echo "=================================="
        echo ""
        
        # Health check results
        echo "HEALTH CHECK:"
        if check_service_health; then
            echo "Status: PASSED"
        else
            echo "Status: FAILED"
        fi
        echo ""
        
        # Performance check results
        echo "PERFORMANCE CHECK:"
        if check_performance; then
            echo "Status: PASSED"
        else
            echo "Status: FAILED"
        fi
        echo ""
        
        # Log check results
        echo "LOG CHECK:"
        if check_logs; then
            echo "Status: PASSED"
        else
            echo "Status: FAILED"
        fi
        echo ""
        
        # Alert check results
        echo "ALERT CHECK:"
        if check_alerts; then
            echo "Status: PASSED"
        else
            echo "Status: FAILED"
        fi
        
    } > "$report_file"
    
    print_success "Monitoring report generated: $report_file"
}

# Main monitoring function
main() {
    print_status "Starting monitoring for $ENVIRONMENT"
    print_status "Check type: $CHECK_TYPE"
    print_status "CPU threshold: ${ALERT_THRESHOLD_CPU}%"
    print_status "Memory threshold: ${ALERT_THRESHOLD_MEMORY}%"
    print_status "Disk threshold: ${ALERT_THRESHOLD_DISK}%"
    
    # Run checks
    check_prerequisites
    check_connectivity
    
    local overall_status=0
    
    # Perform checks based on type
    case "$CHECK_TYPE" in
        "all")
            check_service_health || overall_status=1
            check_performance || overall_status=1
            check_logs || overall_status=1
            check_alerts || overall_status=1
            ;;
        "health")
            check_service_health || overall_status=1
            ;;
        "performance")
            check_performance || overall_status=1
            ;;
        "logs")
            check_logs || overall_status=1
            ;;
        "alerts")
            check_alerts || overall_status=1
            ;;
    esac
    
    # Generate report
    generate_report
    
    # Summary
    echo ""
    print_status "Monitoring Summary:"
    echo "  Environment: $ENVIRONMENT"
    echo "  Check type: $CHECK_TYPE"
    echo "  Status: $([ $overall_status -eq 0 ] && echo "PASSED" || echo "FAILED")"
    
    if [[ $overall_status -eq 0 ]]; then
        print_success "All monitoring checks passed!"
    else
        print_error "Some monitoring checks failed!"
        exit 1
    fi
}

# Run main function
main "$@"
