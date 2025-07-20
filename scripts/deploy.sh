#!/bin/bash

# Tavonga Backend API Deployment Script
# This script handles the deployment of the backend API to production

set -e  # Exit on any error

# Configuration
PROJECT_DIR="/opt/tavonga/backend-api"
VENV_DIR="$PROJECT_DIR/venv"
LOG_FILE="/var/log/tavonga/deploy.log"
BACKUP_DIR="/opt/tavonga/backups"
SERVICE_NAME="tavonga-api"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR $(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING $(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        error "This script should not be run as root for security reasons."
    fi
}

# Create necessary directories
create_directories() {
    log "Creating necessary directories..."
    sudo mkdir -p /var/log/tavonga "$BACKUP_DIR"
    sudo chown -R $USER:$USER /var/log/tavonga "$BACKUP_DIR"
}

# Backup database
backup_database() {
    log "Creating database backup..."
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    
    if [[ -n "${DATABASE_URL}" && "${DATABASE_URL}" =~ postgres:// ]]; then
        pg_dump "${DATABASE_URL}" > "$BACKUP_DIR/db_backup_$TIMESTAMP.sql"
        log "Database backup created: $BACKUP_DIR/db_backup_$TIMESTAMP.sql"
    else
        warning "No PostgreSQL database URL found, skipping database backup"
    fi
}

# Pull latest code
update_code() {
    log "Updating application code..."
    cd "$PROJECT_DIR"
    
    # Backup current version
    if [ -d ".git" ]; then
        git stash push -m "Auto-stash before deployment $(date)"
        git pull origin main
    else
        error "Not a git repository. Please deploy via git."
    fi
}

# Update dependencies
update_dependencies() {
    log "Updating Python dependencies..."
    source "$VENV_DIR/bin/activate"
    pip install --upgrade pip
    pip install -r requirements.txt
}

# Run database migrations
run_migrations() {
    log "Running database migrations..."
    source "$VENV_DIR/bin/activate"
    python manage.py migrate --noinput
}

# Collect static files
collect_static() {
    log "Collecting static files..."
    source "$VENV_DIR/bin/activate"
    python manage.py collectstatic --noinput
}

# Run health checks
health_check() {
    log "Running application health checks..."
    source "$VENV_DIR/bin/activate"
    
    # Check Django configuration
    python manage.py check --deploy
    
    # Check database connectivity
    python manage.py check --database
    
    log "Health checks passed!"
}

# Restart services
restart_services() {
    log "Restarting application services..."
    
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        sudo systemctl restart "$SERVICE_NAME"
        log "Service $SERVICE_NAME restarted"
    else
        warning "Service $SERVICE_NAME is not running"
    fi
    
    # Restart nginx if it exists
    if systemctl is-active --quiet nginx; then
        sudo systemctl reload nginx
        log "Nginx reloaded"
    fi
}

# Verify deployment
verify_deployment() {
    log "Verifying deployment..."
    
    # Wait a moment for services to start
    sleep 5
    
    # Check if service is running
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        log "✓ Service is running"
    else
        error "✗ Service failed to start"
    fi
    
    # Check HTTP response (if available)
    if command -v curl &> /dev/null; then
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/health/ || echo "000")
        if [ "$HTTP_CODE" = "200" ]; then
            log "✓ Health check endpoint responding"
        else
            warning "✗ Health check endpoint not responding (HTTP $HTTP_CODE)"
        fi
    fi
}

# Rollback function
rollback() {
    log "Rolling back to previous version..."
    cd "$PROJECT_DIR"
    git reset --hard HEAD~1
    restart_services
    log "Rollback completed"
}

# Main deployment function
main() {
    log "Starting deployment process..."
    
    check_root
    create_directories
    
    # Check if .env file exists
    if [ ! -f "$PROJECT_DIR/.env" ]; then
        error ".env file not found. Please create it from env.production.example"
    fi
    
    backup_database
    update_code
    update_dependencies
    run_migrations
    collect_static
    health_check
    restart_services
    verify_deployment
    
    log "Deployment completed successfully! 🎉"
}

# Handle command line arguments
case "${1:-deploy}" in
    deploy)
        main
        ;;
    rollback)
        rollback
        ;;
    health)
        health_check
        ;;
    backup)
        backup_database
        ;;
    *)
        echo "Usage: $0 {deploy|rollback|health|backup}"
        exit 1
        ;;
esac 