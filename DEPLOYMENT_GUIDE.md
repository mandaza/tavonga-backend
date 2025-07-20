# 🚀 Tavonga Backend API - Production Deployment Guide

## 📋 Overview

This guide provides comprehensive instructions for deploying the Tavonga Backend API to production. The backend has been prepared with security best practices, containerization, monitoring, and automated deployment capabilities.

## ✅ Deployment Readiness Checklist

### ✅ **COMPLETED: Security Configuration**
- [x] Environment variables configuration (`.env` templates)
- [x] Production security settings (SSL, HSTS, secure cookies)
- [x] Secret key management
- [x] Debug mode disabled for production
- [x] CORS properly configured

### ✅ **COMPLETED: Database Configuration**
- [x] PostgreSQL support via DATABASE_URL
- [x] Connection pooling and health checks
- [x] Migration scripts ready

### ✅ **COMPLETED: Containerization**
- [x] Production-ready Dockerfile
- [x] Docker Compose for local development
- [x] Multi-stage builds for optimization
- [x] Non-root user for security

### ✅ **COMPLETED: Static Files & Media**
- [x] Static files collection configured
- [x] Media storage options (Local/S3/Cloudinary)
- [x] CDN-ready configuration

### ✅ **COMPLETED: Monitoring & Health Checks**
- [x] Health check endpoints (`/api/v1/health/`, `/health/`)
- [x] Readiness and liveness probes for Kubernetes
- [x] Comprehensive logging configuration
- [x] Sentry integration for error tracking

### ✅ **COMPLETED: Deployment Automation**
- [x] Production setup script (`scripts/setup-production.sh`)
- [x] Deployment script (`scripts/deploy.sh`)
- [x] Systemd service configuration
- [x] Nginx configuration with security headers
- [x] Automated backups and log rotation

## 🚀 Quick Start Deployment

### Option 1: Traditional Server Deployment

1. **Run the production setup script:**
   ```bash
   sudo bash scripts/setup-production.sh
   ```

2. **Clone your code:**
   ```bash
   sudo -u tavonga git clone <your-repo> /opt/tavonga/backend-api
   cd /opt/tavonga/backend-api
   ```

3. **Configure environment:**
   ```bash
   cp env.production.example .env
   # Edit .env with your production values
   nano .env
   ```

4. **Install dependencies and setup:**
   ```bash
   sudo -u tavonga bash
   source venv/bin/activate
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py collectstatic --noinput
   ```

5. **Start services:**
   ```bash
   sudo systemctl start tavonga-api nginx
   sudo systemctl enable tavonga-api nginx
   ```

### Option 2: Docker Deployment

1. **Create production environment file:**
   ```bash
   cp env.production.example .env
   # Configure your production values
   ```

2. **Build and run with Docker Compose:**
   ```bash
   docker-compose up -d
   ```

3. **Run migrations:**
   ```bash
   docker-compose exec backend python manage.py migrate
   ```

## 📝 Environment Configuration

### Required Environment Variables

Copy `env.production.example` to `.env` and configure:

```bash
# Security
SECRET_KEY=<generate-a-strong-secret-key>
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,api.yourdomain.com

# Database (PostgreSQL recommended)
DATABASE_URL=postgres://user:password@host:5432/database

# Storage (S3 recommended for production)
STORAGE_BACKEND=s3
AWS_ACCESS_KEY_ID=<your-access-key>
AWS_SECRET_ACCESS_KEY=<your-secret-key>
AWS_STORAGE_BUCKET_NAME=<your-bucket>

# CORS
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# Monitoring
SENTRY_DSN=<your-sentry-dsn>
```

### Generate Secret Key

```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

## 🗄️ Database Setup

### PostgreSQL Setup

1. **Install PostgreSQL:**
   ```bash
   sudo apt install postgresql postgresql-contrib
   ```

2. **Create database and user:**
   ```sql
   sudo -u postgres psql
   CREATE DATABASE tavonga_production;
   CREATE USER tavonga_user WITH PASSWORD 'secure_password';
   GRANT ALL PRIVILEGES ON DATABASE tavonga_production TO tavonga_user;
   \q
   ```

3. **Update DATABASE_URL in .env:**
   ```
   DATABASE_URL=postgres://tavonga_user:secure_password@localhost:5432/tavonga_production
   ```

## 📦 Dependencies

### System Requirements
- Python 3.11+
- PostgreSQL 13+
- Redis 6+ (optional, for caching)
- Nginx
- SSL certificates (Let's Encrypt recommended)

### Python Dependencies
All dependencies are in `requirements.txt` including:
- Django 5.2.3
- Django REST Framework
- PostgreSQL adapter (psycopg2)
- Gunicorn (WSGI server)
- Production utilities (sentry-sdk, whitenoise, etc.)

## 🔒 Security Configuration

### SSL Setup with Certbot

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d yourdomain.com -d api.yourdomain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

### Security Headers

The Nginx configuration includes:
- HSTS headers
- Content Security Policy
- X-Frame-Options
- X-XSS-Protection
- X-Content-Type-Options

## 📊 Monitoring & Logging

### Health Check Endpoints

- `GET /api/v1/health/` - Comprehensive health check
- `GET /api/v1/ready/` - Readiness probe (for Kubernetes)
- `GET /api/v1/live/` - Liveness probe (for Kubernetes)
- `GET /health/` - Simple health check (for load balancers)

### Log Files

- Application logs: `/var/log/tavonga/django.log`
- Gunicorn logs: `/var/log/tavonga/gunicorn.log`
- Access logs: `/var/log/tavonga/access.log`
- Nginx logs: `/var/log/nginx/`

### Backup System

Automated daily backups at 2 AM:
- Database dumps (compressed)
- Media file archives
- Automatic cleanup (7-day retention)

Manual backup: `/usr/local/bin/tavonga-backup`

## 🚀 Deployment Process

### Automated Deployment

Use the deployment script for zero-downtime deployments:

```bash
# Deploy latest version
./scripts/deploy.sh

# Health check only
./scripts/deploy.sh health

# Emergency rollback
./scripts/deploy.sh rollback

# Manual backup
./scripts/deploy.sh backup
```

### Manual Deployment Steps

1. **Backup database:**
   ```bash
   pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql
   ```

2. **Pull latest code:**
   ```bash
   git pull origin main
   ```

3. **Update dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

5. **Collect static files:**
   ```bash
   python manage.py collectstatic --noinput
   ```

6. **Restart services:**
   ```bash
   sudo systemctl restart tavonga-api
   sudo systemctl reload nginx
   ```

## 🔧 Troubleshooting

### Common Issues

1. **Service won't start:**
   ```bash
   sudo systemctl status tavonga-api
   sudo journalctl -u tavonga-api -f
   ```

2. **Database connection issues:**
   ```bash
   # Test database connectivity
   python manage.py check --database
   ```

3. **Static files not loading:**
   ```bash
   python manage.py collectstatic --noinput
   sudo systemctl reload nginx
   ```

4. **Permission issues:**
   ```bash
   sudo chown -R tavonga:tavonga /opt/tavonga/backend-api
   ```

### Health Check Commands

```bash
# Check application health
curl http://localhost:8000/api/v1/health/

# Check service status
sudo systemctl status tavonga-api nginx

# View recent logs
sudo tail -f /var/log/tavonga/django.log
```

## 📈 Performance Optimization

### Gunicorn Configuration

The production setup uses:
- 3 worker processes
- Sync worker class
- 120-second timeout
- Connection keep-alive

### Database Optimization

- Connection pooling enabled
- Query optimization via Django ORM
- Database indexes on frequently queried fields

### Caching Strategy

- Redis for session storage (optional)
- Static file caching via Nginx
- CDN integration for media files

## 🔐 Security Best Practices

### Implemented Security Measures

1. **Application Security:**
   - SECRET_KEY from environment
   - DEBUG=False in production
   - CSRF and XSS protection
   - SQL injection prevention via ORM

2. **Infrastructure Security:**
   - Non-root user for application
   - SSL/TLS encryption
   - Security headers via Nginx
   - Regular security updates

3. **Data Security:**
   - Database connection encryption
   - Secure file uploads
   - Input validation and sanitization

### Security Checklist

- [ ] Update default passwords
- [ ] Configure firewall (UFW)
- [ ] Set up fail2ban
- [ ] Regular security updates
- [ ] Monitor access logs
- [ ] Backup encryption

## 📞 Support & Maintenance

### Regular Maintenance Tasks

1. **Weekly:**
   - Review application logs
   - Check disk space
   - Verify backups

2. **Monthly:**
   - Security updates
   - Certificate renewal check
   - Performance review

3. **Quarterly:**
   - Dependency updates
   - Security audit
   - Backup restore test

### Emergency Contacts

- System Administrator: [Contact Info]
- Database Administrator: [Contact Info]
- Security Team: [Contact Info]

## 🎯 Next Steps

After successful deployment:

1. **Configure monitoring alerts**
2. **Set up CI/CD pipeline**
3. **Load testing**
4. **Performance monitoring**
5. **Security scanning**
6. **Documentation updates**

---

## 📚 Additional Resources

- [Django Deployment Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)
- [Gunicorn Configuration](https://docs.gunicorn.org/en/stable/configure.html)
- [Nginx Security Headers](https://securityheaders.com/)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)

**🎉 Your Tavonga Backend API is now ready for production deployment!** 