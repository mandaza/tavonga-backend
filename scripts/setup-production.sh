#!/bin/bash

# Tavonga Backend API Production Setup Script
# This script sets up the production environment from scratch

set -e

# Configuration
APP_USER="tavonga"
APP_DIR="/opt/tavonga/backend-api"
SERVICE_NAME="tavonga-api"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   error "This script must be run as root for initial setup"
fi

# Update system packages
log "Updating system packages..."
apt-get update && apt-get upgrade -y

# Install system dependencies
log "Installing system dependencies..."
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    postgresql-client \
    redis-tools \
    nginx \
    supervisor \
    curl \
    git \
    htop \
    certbot \
    python3-certbot-nginx

# Create application user
log "Creating application user..."
if ! id "$APP_USER" &>/dev/null; then
    useradd --system --create-home --shell /bin/bash "$APP_USER"
    log "User $APP_USER created"
else
    log "User $APP_USER already exists"
fi

# Create application directory
log "Creating application directory..."
mkdir -p "$APP_DIR"
chown -R "$APP_USER:$APP_USER" "$APP_DIR"

# Create log directories
log "Creating log directories..."
mkdir -p /var/log/tavonga
chown -R "$APP_USER:$APP_USER" /var/log/tavonga

# Switch to app user for the rest of the setup
log "Switching to application user..."
sudo -u "$APP_USER" bash << 'EOF'
set -e

APP_DIR="/opt/tavonga/backend-api"
cd "$APP_DIR"

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

echo "Virtual environment created successfully"
EOF

# Create systemd service file
log "Creating systemd service..."
cat > /etc/systemd/system/${SERVICE_NAME}.service << EOF
[Unit]
Description=Tavonga Backend API
After=network.target postgresql.service redis.service
Wants=postgresql.service redis.service

[Service]
Type=exec
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/venv/bin/gunicorn \\
    --bind 127.0.0.1:8000 \\
    --workers 3 \\
    --worker-class sync \\
    --worker-connections 1000 \\
    --max-requests 1000 \\
    --timeout 120 \\
    --keep-alive 2 \\
    --user $APP_USER \\
    --group $APP_USER \\
    --log-level info \\
    --log-file /var/log/tavonga/gunicorn.log \\
    --access-logfile /var/log/tavonga/access.log \\
    core.wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create nginx configuration
log "Creating nginx configuration..."
cat > /etc/nginx/sites-available/tavonga-api << 'EOF'
server {
    listen 80;
    server_name _;  # Replace with your domain
    
    client_max_body_size 100M;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    
    # Static files
    location /static/ {
        alias /opt/tavonga/backend-api/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Media files
    location /media/ {
        alias /opt/tavonga/backend-api/media/;
        expires 1y;
        add_header Cache-Control "public";
    }
    
    # API endpoints
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Health check
    location /health {
        access_log off;
        proxy_pass http://127.0.0.1:8000/api/v1/health/;
    }
}
EOF

# Enable nginx site
ln -sf /etc/nginx/sites-available/tavonga-api /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
nginx -t

# Create backup script
log "Creating backup script..."
cat > /usr/local/bin/tavonga-backup << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/tavonga/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

# Backup database if PostgreSQL is configured
if [[ -n "${DATABASE_URL}" && "${DATABASE_URL}" =~ postgres:// ]]; then
    pg_dump "${DATABASE_URL}" > "$BACKUP_DIR/db_backup_$TIMESTAMP.sql"
    gzip "$BACKUP_DIR/db_backup_$TIMESTAMP.sql"
fi

# Backup media files
tar -czf "$BACKUP_DIR/media_backup_$TIMESTAMP.tar.gz" -C /opt/tavonga/backend-api media/

# Clean old backups (keep 7 days)
find "$BACKUP_DIR" -name "*.gz" -mtime +7 -delete
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +7 -delete

echo "Backup completed: $TIMESTAMP"
EOF

chmod +x /usr/local/bin/tavonga-backup

# Create daily backup cron job
log "Setting up daily backups..."
cat > /etc/cron.d/tavonga-backup << 'EOF'
# Daily backup at 2 AM
0 2 * * * tavonga /usr/local/bin/tavonga-backup >> /var/log/tavonga/backup.log 2>&1
EOF

# Create log rotation configuration
log "Setting up log rotation..."
cat > /etc/logrotate.d/tavonga << 'EOF'
/var/log/tavonga/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 tavonga tavonga
    postrotate
        systemctl reload tavonga-api
    endscript
}
EOF

# Reload systemd and enable services
log "Enabling services..."
systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
systemctl enable nginx

log "Production setup completed!"
log "Next steps:"
log "1. Clone your code to $APP_DIR"
log "2. Copy env.production.example to $APP_DIR/.env and configure it"
log "3. Install dependencies: cd $APP_DIR && source venv/bin/activate && pip install -r requirements.txt"
log "4. Run migrations: python manage.py migrate"
log "5. Collect static files: python manage.py collectstatic"
log "6. Start services: systemctl start $SERVICE_NAME nginx"
log "7. Configure SSL with: certbot --nginx -d yourdomain.com" 