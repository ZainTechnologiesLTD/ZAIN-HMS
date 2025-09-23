# 🚀 ZAIN HMS Deployment Guide

## 📋 Overview
This guide consolidates all deployment information for the ZAIN HMS project, including production deployment, server setup, and maintenance procedures.

## 🎯 Quick Deployment

### Prerequisites
- Ubuntu 20.04+ server
- Python 3.12
- PostgreSQL 13+
- Redis 6.0+
- Nginx

### One-Command Deployment
```bash
chmod +x deploy_production.sh
./deploy_production.sh
```

## 🔧 Manual Deployment Steps

### 1. Server Preparation
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.12
sudo apt install python3.12 python3.12-venv python3.12-dev -y

# Install PostgreSQL and Redis
sudo apt install postgresql postgresql-contrib redis-server -y

# Install Nginx
sudo apt install nginx -y
```

### 2. Database Setup
```bash
# Create database
sudo -u postgres createdb zain_hms
sudo -u postgres createuser zain_hms_user
sudo -u postgres psql -c "ALTER USER zain_hms_user WITH PASSWORD 'secure_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE zain_hms TO zain_hms_user;"
```

### 3. Application Deployment
```bash
# Clone repository
git clone https://github.com/Zain-Technologies-22/ZAIN-HMS.git
cd ZAIN-HMS

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.template .env
# Edit .env with your settings

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Create superuser
python manage.py createsuperuser
```

### 4. Production Server Setup
```bash
# Install Gunicorn
pip install gunicorn

# Create systemd service
sudo cp deployment/zain_hms.service /etc/systemd/system/
sudo systemctl enable zain_hms
sudo systemctl start zain_hms

# Configure Nginx
sudo cp deployment/nginx.conf /etc/nginx/sites-available/zain_hms
sudo ln -s /etc/nginx/sites-available/zain_hms /etc/nginx/sites-enabled/
sudo systemctl reload nginx
```

## 🔄 Branch Strategy

### Production Workflow
1. **Development Branch** - Active development
2. **Main Branch** - Production releases
3. **Feature Branches** - Individual features

### Deployment Process
```bash
# Switch to main branch
git checkout main

# Pull latest changes
git pull origin main

# Deploy to production
./deploy_production.sh
```

## 🛠️ Maintenance

### Regular Updates
```bash
# Update dependencies
pip install --upgrade -r requirements.txt

# Run migrations
python manage.py migrate

# Restart services
sudo systemctl restart zain_hms
```

### Backup Procedures
```bash
# Database backup
pg_dump zain_hms > backup_$(date +%Y%m%d_%H%M%S).sql

# Media files backup
tar -czf media_backup_$(date +%Y%m%d_%H%M%S).tar.gz media/
```

## 🔍 Monitoring

### Health Checks
- Application: `https://your-domain.com/health/`
- Database: `python manage.py check --database default`
- Redis: `redis-cli ping`

### Logs
- Application: `journalctl -u zain_hms -f`
- Nginx: `tail -f /var/log/nginx/error.log`
- Django: `tail -f logs/django.log`

## ⚡ Performance Optimization

### Production Settings
- Debug disabled
- Static files served by Nginx
- Database connection pooling
- Redis caching enabled
- Gzip compression

### Security Features
- HTTPS/SSL enabled
- CSRF protection
- SQL injection protection
- XSS protection
- Security headers configured

---

For detailed server setup instructions, see `docs/SETUP_GUIDE.md`  
For version management, see `docs/VERSION_MANAGEMENT_GUIDE.md`