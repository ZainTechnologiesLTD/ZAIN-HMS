# 🚀 ZAIN HMS Complete Production Deployment Guide

**Bismillahir Rahmanir Raheem**

This comprehensive guide covers the complete production deployment of ZAIN HMS using a 3-container scalable architecture (NGINX → Django → PostgreSQL) with automated CI/CD pipeline.

## 📋 Table of Contents

1. [Pre-Deployment Requirements](#pre-deployment-requirements)
2. [Server Setup and Preparation](#server-setup-and-preparation)
3. [Docker Container Architecture](#docker-container-architecture)
4. [GitHub Actions CI/CD Setup](#github-actions-cicd-setup)
5. [Manual Deployment Process](#manual-deployment-process)
6. [Automated Deployment Process](#automated-deployment-process)
7. [SSL/HTTPS Configuration](#sslhttps-configuration)
8. [Monitoring and Maintenance](#monitoring-and-maintenance)
9. [Troubleshooting](#troubleshooting)
10. [Security Best Practices](#security-best-practices)

## 🎯 Pre-Deployment Requirements

### Server Requirements

- **Operating System**: Ubuntu 20.04+ LTS
- **RAM**: Minimum 4GB (8GB+ recommended)
- **Storage**: Minimum 50GB SSD
- **Network**: Public IP address with SSH access
- **Domain**: Valid domain name (optional but recommended)

### Local Development Requirements

- Git installed and configured
- Docker and Docker Compose installed locally (for testing)
- SSH access to production server
- GitHub repository access

### Accounts and Services

- GitHub repository with admin access
- Domain registrar access (for DNS configuration)
- Email service (Gmail, SendGrid, etc.)
- AWS account (optional, for S3 storage)
- SSL certificate provider or Let's Encrypt

## 🖥️ Server Setup and Preparation

### Option 1: Automated Server Setup

Use the provided script to automatically configure your Ubuntu server:

```bash
# On your local machine
scp scripts/setup-production-server.sh root@YOUR_SERVER_IP:/tmp/
ssh root@YOUR_SERVER_IP "chmod +x /tmp/setup-production-server.sh && /tmp/setup-production-server.sh yourdomain.com"
```

### Option 2: Manual Server Setup

If you prefer manual setup, follow these steps:

#### 1. Update System

```bash
sudo apt update && sudo apt upgrade -y
```

#### 2. Install Docker

```bash
# Remove old versions
sudo apt remove docker docker-engine docker.io containerd runc

# Install prerequisites
sudo apt install apt-transport-https ca-certificates curl gnupg lsb-release

# Add Docker's official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Add Docker repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt update
sudo apt install docker-ce docker-ce-cli containerd.io docker-compose-plugin
```

#### 3. Install Docker Compose

```bash
# Install latest Docker Compose
LATEST_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep tag_name | cut -d '"' -f 4)
sudo curl -L "https://github.com/docker/compose/releases/download/${LATEST_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### 4. Create Application User

```bash
# Create dedicated user for ZAIN HMS
sudo useradd -m -s /bin/bash zain-hms
sudo usermod -aG docker zain-hms
```

#### 5. Setup Directory Structure

```bash
# Create application directories
sudo mkdir -p /opt/zain_hms/{data/{postgres,redis,static,media},logs,backups,ssl}
sudo chown -R zain-hms:zain-hms /opt/zain_hms
sudo chmod -R 755 /opt/zain_hms
sudo chmod -R 700 /opt/zain_hms/ssl
```

## 🐳 Docker Container Architecture

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        NGINX Container                       │
│                    (Reverse Proxy/Load Balancer)           │
│                     Ports: 80, 443                         │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                    Django Web Container                     │
│                  (Gunicorn + Django App)                   │
│                       Port: 8000                           │
└─────────────────────┬───────────────┬─────────────────────┘
                      │               │
          ┌───────────▼──────────┐   ┌▼──────────────────┐
          │  PostgreSQL Container │   │  Redis Container │
          │     (Database)       │   │     (Cache)      │
          │      Port: 5432      │   │   Port: 6379     │
          └──────────────────────┘   └──────────────────┘
```

### Container Specifications

#### NGINX Container
- **Image**: `nginx:alpine`
- **Purpose**: Reverse proxy, SSL termination, static file serving
- **Scaling**: Single instance (can be load-balanced externally)

#### Django Web Container
- **Image**: Custom built from `docker/Dockerfile.prod`
- **Purpose**: Django application server
- **Scaling**: 2+ instances for high availability

#### PostgreSQL Container
- **Image**: `postgres:15-alpine`
- **Purpose**: Primary database
- **Scaling**: Single instance (clustering possible)

#### Redis Container
- **Image**: `redis:7-alpine`
- **Purpose**: Cache and session storage
- **Scaling**: Single instance (clustering possible)

## 🔧 GitHub Actions CI/CD Setup

### 1. Configure Repository Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions, and add these secrets:

#### Server Connection
- `PRODUCTION_SERVER_IP`: Your server's IP address
- `PRODUCTION_SERVER_USER`: SSH username (typically `root` or `ubuntu`)
- `PRODUCTION_SSH_KEY`: SSH private key content

#### Application Configuration
- `SECRET_KEY`: 50+ character Django secret key
- `ALLOWED_HOSTS`: Comma-separated list of allowed domains/IPs
- `MAIN_DOMAIN`: Your primary domain name

#### Database Configuration
- `DB_NAME`: `zain_hms`
- `DB_USER`: `zain_hms_user`
- `DB_PASSWORD`: Strong database password

#### Email Configuration
- `EMAIL_HOST`: SMTP server (e.g., `smtp.gmail.com`)
- `EMAIL_HOST_USER`: Email username
- `EMAIL_HOST_PASSWORD`: Email password or app-specific password

#### Optional Services
- `AWS_ACCESS_KEY_ID`: AWS access key (for S3 storage)
- `AWS_SECRET_ACCESS_KEY`: AWS secret key
- `SLACK_WEBHOOK_URL`: Slack webhook for notifications

### 2. Generate SSH Keys

```bash
# Generate SSH key pair for GitHub Actions
ssh-keygen -t ed25519 -f github_actions_key -C "github-actions@zainhms.com"

# Add public key to server
ssh-copy-id -i github_actions_key.pub root@YOUR_SERVER_IP

# Copy private key content to GitHub secret PRODUCTION_SSH_KEY
cat github_actions_key
```

### 3. Enable CI/CD Workflow

The workflow is automatically triggered when:
- Code is pushed to `main` or `production` branch
- A release is published
- Pull requests are opened to `main` branch

## 📦 Manual Deployment Process

### 1. Prepare Production Files

```bash
# Clone repository
cd /opt/zain_hms
git clone https://github.com/Zain-Technologies-22/ZAIN-HMS.git .

# Copy production configuration
cp docker-compose.prod.yml docker-compose.yml
cp .env.production.template .env.prod
```

### 2. Configure Environment

Edit `/opt/zain_hms/.env.prod` with your production values:

```bash
sudo nano /opt/zain_hms/.env.prod
```

Key configurations:
```env
SECRET_KEY=your-50-character-secret-key
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,your-server-ip
DB_PASSWORD=your-secure-database-password
REDIS_PASSWORD=your-secure-redis-password
EMAIL_HOST_PASSWORD=your-email-password
```

### 3. Deploy Application

```bash
# Make deploy script executable
chmod +x deploy.sh

# Run deployment
sudo -u zain-hms ./deploy.sh
```

### 4. Verify Deployment

```bash
# Check container status
docker-compose ps

# Check application health
curl http://localhost/health/

# Check logs
docker-compose logs -f web
```

## 🤖 Automated Deployment Process

### Using GitHub Actions (Recommended)

1. **Push to Production Branch**: 
   ```bash
   git checkout production
   git merge main
   git push origin production
   ```

2. **Monitor Deployment**: Check GitHub Actions tab in your repository

3. **Verify Deployment**: Check deployment logs and application health

### Using Automated Script

```bash
# From your local machine
./scripts/automated-deploy.sh -s YOUR_SERVER_IP -d yourdomain.com
```

Options:
- `-s, --server`: Production server IP (required)
- `-u, --user`: SSH user (default: root)
- `-d, --domain`: Domain name (default: localhost)
- `-k, --key`: SSH private key path
- `-e, --env`: Environment (default: production)

## 🔒 SSL/HTTPS Configuration

### Option 1: Let's Encrypt (Recommended)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Set up auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### Option 2: Custom SSL Certificate

1. Place certificate files in `/opt/zain_hms/ssl/`
2. Update NGINX configuration to use custom certificates
3. Restart NGINX container

### Option 3: Cloudflare SSL (Flexible)

1. Configure Cloudflare for your domain
2. Enable SSL/TLS encryption in Cloudflare
3. Update DNS to point to your server
4. NGINX will receive HTTP traffic from Cloudflare

## 📊 Monitoring and Maintenance

### Health Monitoring

```bash
# Check application health
curl http://yourdomain.com/health/

# Monitor container resources
docker stats

# Check container logs
docker-compose logs -f --tail=100 web
docker-compose logs -f --tail=100 db
docker-compose logs -f --tail=100 nginx
```

### Database Maintenance

```bash
# Create manual backup
docker-compose exec db pg_dump -U zain_hms_user zain_hms > backup_$(date +%Y%m%d).sql

# Monitor database performance
docker-compose exec db psql -U zain_hms_user -d zain_hms -c "SELECT * FROM pg_stat_activity;"

# Clean up old data (customize as needed)
docker-compose exec web python manage.py cleanup_old_data
```

### Log Management

```bash
# Rotate logs manually
sudo logrotate /etc/logrotate.d/zain-hms

# Check log sizes
du -sh /opt/zain_hms/logs/*

# Archive old logs
find /opt/zain_hms/logs -name "*.log" -mtime +30 -exec gzip {} \;
```

### Update Process

```bash
# Update from GitHub (manual)
cd /opt/zain_hms
git pull origin production
docker-compose pull
docker-compose up -d --remove-orphans

# Update using deployment script
sudo -u zain-hms ./deploy.sh
```

## 🚨 Troubleshooting

### Common Issues and Solutions

#### 1. Container Won't Start

```bash
# Check container logs
docker-compose logs container_name

# Check Docker daemon
sudo systemctl status docker

# Restart Docker service
sudo systemctl restart docker
```

#### 2. Database Connection Issues

```bash
# Check database logs
docker-compose logs db

# Test database connection
docker-compose exec web python manage.py dbshell

# Reset database password
docker-compose exec db psql -U postgres -c "ALTER USER zain_hms_user WITH PASSWORD 'newpassword';"
```

#### 3. NGINX Configuration Issues

```bash
# Test NGINX configuration
docker-compose exec nginx nginx -t

# Reload NGINX configuration
docker-compose exec nginx nginx -s reload

# Check NGINX logs
docker-compose logs nginx
```

#### 4. SSL Certificate Issues

```bash
# Check certificate expiry
openssl x509 -in /etc/letsencrypt/live/yourdomain.com/cert.pem -text -noout | grep "Not After"

# Renew Let's Encrypt certificate
sudo certbot renew

# Test SSL configuration
curl -I https://yourdomain.com
```

#### 5. Performance Issues

```bash
# Monitor resource usage
htop
df -h
docker stats

# Check database performance
docker-compose exec db psql -U zain_hms_user -d zain_hms -c "SELECT * FROM pg_stat_user_tables;"

# Optimize database
docker-compose exec web python manage.py optimize_db
```

### Emergency Procedures

#### Rollback Deployment

```bash
# Stop current containers
docker-compose down

# Restore from backup
docker-compose exec db psql -U zain_hms_user -d zain_hms < backup_file.sql

# Deploy previous version
git checkout previous_version_tag
docker-compose up -d
```

#### Database Recovery

```bash
# Stop application
docker-compose stop web

# Restore database
docker-compose exec db psql -U zain_hms_user -d zain_hms < backup_file.sql

# Start application
docker-compose start web
```

## 🛡️ Security Best Practices

### 1. Server Security

```bash
# Configure firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# Install Fail2ban
sudo apt install fail2ban
sudo systemctl enable fail2ban
```

### 2. Application Security

- Use strong, unique passwords for all services
- Enable HTTPS/SSL encryption
- Regularly update dependencies
- Monitor security advisories
- Implement proper backup strategies
- Use environment variables for sensitive data

### 3. Database Security

```bash
# Regular security updates
docker-compose exec db apt update && apt upgrade -y

# Monitor database access logs
docker-compose logs db | grep "authentication"

# Backup encryption
gpg --cipher-algo AES256 --compress-algo 1 --s2k-mode 3 --s2k-digest-algo SHA512 --s2k-count 65536 --symmetric backup.sql
```

### 4. Monitoring and Alerting

Set up monitoring for:
- Container health and resource usage
- Database performance and connectivity
- Application response times
- SSL certificate expiry
- Disk space and memory usage
- Security events and failed login attempts

## 📞 Support and Maintenance

### Regular Maintenance Tasks

**Daily:**
- Monitor application health
- Check container logs for errors
- Verify backup completion

**Weekly:**
- Review resource usage
- Update system packages
- Clean up old logs and files
- Review security logs

**Monthly:**
- Update Docker images
- Review and rotate secrets
- Performance optimization
- Security audit

### Getting Help

1. **Documentation**: Check this guide and other docs in `/docs/`
2. **Logs**: Always check container logs first
3. **Community**: Search for similar issues online
4. **Professional Support**: Contact system administrators

### Contact Information

- **Technical Support**: admin@yourdomain.com
- **Emergency Contact**: +1-XXX-XXX-XXXX
- **DevOps Team**: devops@yourdomain.com

---

**May Allah bless this project and make it beneficial for healthcare services. Ameen.**

*Last updated: $(date)*