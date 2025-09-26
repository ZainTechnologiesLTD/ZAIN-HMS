# 📦 ZAIN HMS Downloadable Software Installation Guide

**Bismillahir Rahmanir Raheem**

Welcome to the comprehensive installation guide for ZAIN HMS (Hospital Management System). This guide covers all installation methods and provides complete instructions for deploying ZAIN HMS as downloadable software from GitHub.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation Methods](#installation-methods)
3. [Quick Installation](#quick-installation)
4. [Interactive Installation](#interactive-installation)
5. [Offline Installation](#offline-installation)
6. [Post-Installation Setup](#post-installation-setup)
7. [Configuration Guide](#configuration-guide)
8. [Troubleshooting](#troubleshooting)
9. [Maintenance](#maintenance)
10. [Security](#security)

## 🎯 Prerequisites

### System Requirements

#### Minimum Requirements
- **Operating System**: Ubuntu 18.04+ / CentOS 7+ / Debian 9+ / Rocky Linux 8+
- **RAM**: 2GB (4GB recommended)
- **Storage**: 20GB free space (50GB recommended)
- **CPU**: 2 cores (4+ cores recommended)
- **Network**: Internet connection for initial setup
- **Access**: Root/sudo privileges

#### Production Requirements
- **Operating System**: Ubuntu 20.04 LTS / CentOS Stream 8+
- **RAM**: 8GB+ (16GB recommended)
- **Storage**: 100GB+ SSD
- **CPU**: 4+ cores (8+ cores recommended)
- **Network**: Static IP, domain name, SSL certificate
- **Access**: Dedicated server or VPS

### Software Dependencies
The installation scripts will automatically install these if not present:
- Docker Engine 20.10+
- Docker Compose 2.0+
- Git
- Curl/Wget
- Basic system utilities

## 🚀 Installation Methods

ZAIN HMS offers three installation methods to suit different needs:

### Method 1: Quick Installation (Recommended)
**Best for**: First-time users, development environments
- One command installation
- Automatic dependency detection
- Interactive configuration
- Takes 10-15 minutes

### Method 2: Interactive Installation
**Best for**: Users who want step-by-step guidance
- Beautiful terminal interface
- Guided configuration
- Real-time progress tracking
- User-friendly menus

### Method 3: Offline Installation
**Best for**: Servers without internet, air-gapped environments
- Complete offline package
- All dependencies included
- No internet required after download
- Enterprise-ready

## 🎯 Quick Installation

### Step 1: Download and Run Installer

```bash
# Download and run the quick installer
curl -fsSL https://raw.githubusercontent.com/ZainTechnologiesLTD/ZAIN-HMS/main/install.sh | sudo bash
```

**Alternative download methods:**

```bash
# Method 1: Direct download
wget https://raw.githubusercontent.com/ZainTechnologiesLTD/ZAIN-HMS/main/install.sh
sudo chmod +x install.sh
sudo ./install.sh

# Method 2: Clone repository
git clone https://github.com/ZainTechnologiesLTD/ZAIN-HMS.git
cd ZAIN-HMS
sudo ./install.sh

# Method 3: With custom domain
curl -fsSL https://raw.githubusercontent.com/ZainTechnologiesLTD/ZAIN-HMS/main/install.sh | sudo bash -s yourdomain.com
```

### Step 2: Follow Installation Progress

The installer will:
1. ✅ Check system requirements
2. 📦 Install Docker and Docker Compose
3. 🔧 Configure system settings
4. 🏥 Download and setup ZAIN HMS
5. 🚀 Start all services
6. 🎉 Complete installation

### Step 3: Access Your System

After installation completes:
- **Web Interface**: `http://YOUR_SERVER_IP`
- **Admin Panel**: `http://YOUR_SERVER_IP/admin/`
- **Default Login**: `admin` / `admin123`

## 🎨 Interactive Installation

For users who prefer a guided installation with beautiful terminal interface:

### Step 1: Download Interactive Installer

```bash
# Download interactive installer
wget https://raw.githubusercontent.com/ZainTechnologiesLTD/ZAIN-HMS/main/install-interactive.sh
chmod +x install-interactive.sh
sudo ./install-interactive.sh
```

### Step 2: Use the Interactive Interface

The interactive installer provides:
- 🎨 Beautiful ASCII art interface
- 📋 Step-by-step configuration menus
- 📊 Real-time progress bars
- 🔧 Advanced configuration options
- ❓ Built-in help and documentation

### Configuration Options Available:
- Domain name and SSL setup
- Database configuration
- Security settings
- Performance tuning
- Backup configuration
- Monitoring setup

## 💾 Offline Installation

For environments without internet access or enterprise deployments:

### Step 1: Create Offline Package (On Internet-Connected Machine)

```bash
# Clone repository and create offline package
git clone https://github.com/ZainTechnologiesLTD/ZAIN-HMS.git
cd ZAIN-HMS
sudo ./scripts/create-offline-package.sh
```

This creates: `zain-hms-offline-installer.tar.gz` (~2GB)

### Step 2: Transfer to Target Server

```bash
# Transfer the package to your server
scp zain-hms-offline-installer.tar.gz user@your-server:/tmp/
```

### Step 3: Install Offline

```bash
# On the target server
cd /tmp
tar -xzf zain-hms-offline-installer.tar.gz
cd zain-hms-offline-installer
sudo ./install-offline.sh
```

### Offline Package Contents:
- All Docker images (pre-downloaded)
- System packages for Ubuntu/CentOS
- Application code and configuration
- Complete documentation
- Installation scripts

## ⚙️ Post-Installation Setup

### 1. First Login and Security

```bash
# Access web interface
http://YOUR_SERVER_IP

# Default credentials
Username: admin
Password: admin123
```

**🔒 IMPORTANT**: Change default password immediately!

### 2. Basic Configuration

1. **Update Admin Profile**:
   - Go to Admin Panel → Users → admin
   - Change password, email, and personal information

2. **Configure System Settings**:
   - Hospital information
   - Timezone and locale
   - Email settings
   - Backup preferences

3. **Create Users**:
   - Doctors
   - Nurses
   - Administrative staff
   - Department heads

### 3. Data Import (Optional)

If you have existing data:
```bash
# Access maintenance tools
sudo /opt/zain-hms/scripts/zain-hms-maintenance.sh

# Select: Database Operations → Import Data
```

## 🔧 Configuration Guide

### Environment Variables

Main configuration file: `/opt/zain-hms/.env.prod`

```bash
# Database Configuration
DB_NAME=zain_hms
DB_USER=zain_hms
DB_PASSWORD=your-secure-password
DB_HOST=db
DB_PORT=5432

# Redis Configuration  
REDIS_URL=redis://:your-redis-password@redis:6379/1

# Django Configuration
SECRET_KEY=your-50-character-secret-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### SSL Certificate Setup

#### Method 1: Let's Encrypt (Recommended)

```bash
# Run SSL setup
sudo /opt/zain-hms/scripts/setup-ssl.sh yourdomain.com
```

#### Method 2: Custom Certificate

```bash
# Copy your certificates
sudo cp your-cert.crt /opt/zain-hms/ssl/
sudo cp your-private.key /opt/zain-hms/ssl/
sudo chown zain-hms:zain-hms /opt/zain-hms/ssl/*
```

### Firewall Configuration

```bash
# Configure firewall
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP
sudo ufw allow 443/tcp     # HTTPS
sudo ufw --force enable
```

### Performance Tuning

Edit `/opt/zain-hms/docker-compose.prod.yml`:

```yaml
# For high-traffic environments
services:
  web:
    deploy:
      replicas: 3  # Scale web servers
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G
```

## 🔍 Troubleshooting

### Common Issues and Solutions

#### 1. Installation Fails

```bash
# Check system requirements
sudo ./scripts/check-requirements.sh

# Check Docker installation
docker --version
docker-compose --version

# Check logs
tail -f /var/log/zain-hms-installation.log
```

#### 2. Services Won't Start

```bash
# Check service status
sudo systemctl status zain-hms

# Check Docker containers
cd /opt/zain-hms
sudo docker-compose -f docker-compose.prod.yml ps

# Restart services
sudo systemctl restart zain-hms
```

#### 3. Database Connection Issues

```bash
# Check database container
sudo docker-compose -f /opt/zain-hms/docker-compose.prod.yml logs db

# Reset database password
sudo /opt/zain-hms/scripts/zain-hms-maintenance.sh
# Select: Database Operations → Change Database Password
```

#### 4. Web Interface Not Accessible

```bash
# Check NGINX configuration
sudo docker-compose -f /opt/zain-hms/docker-compose.prod.yml logs nginx

# Check firewall
sudo ufw status

# Test local connection
curl http://localhost/health/
```

#### 5. SSL Certificate Problems

```bash
# Renew Let's Encrypt certificate
sudo certbot renew

# Check certificate status
sudo certbot certificates

# Test SSL configuration
openssl s_client -connect yourdomain.com:443
```

### Log Files

Monitor these log files for troubleshooting:

```bash
# Application logs
sudo tail -f /opt/zain-hms/logs/django.log
sudo tail -f /opt/zain-hms/logs/nginx.log

# Docker logs
sudo docker-compose -f /opt/zain-hms/docker-compose.prod.yml logs -f

# System logs
sudo tail -f /var/log/syslog
sudo tail -f /var/log/zain-hms-maintenance.log
```

### Performance Issues

```bash
# Check system resources
htop
free -h
df -h

# Analyze Docker container resources
sudo docker stats

# Database performance
sudo docker-compose -f /opt/zain-hms/docker-compose.prod.yml exec db psql -U zain_hms -d zain_hms -c "\dt+"
```

## 🔧 Maintenance

### Regular Maintenance Tasks

#### Daily
- Monitor system health
- Check log files
- Verify backup completion

#### Weekly
- Update system packages
- Clean old log files
- Review security logs

#### Monthly
- Update ZAIN HMS
- Clean old backups
- Performance review
- Security audit

### Maintenance Tools

Access the comprehensive maintenance interface:

```bash
sudo /opt/zain-hms/scripts/zain-hms-maintenance.sh
```

Available maintenance options:
- 🔄 System updates
- 💾 Backup and restore
- 🔧 Database maintenance
- 📊 Performance monitoring
- 🔒 Security audits
- 🧹 Log cleanup
- ⚙️ Configuration updates

### Backup and Recovery

#### Automated Backups

```bash
# Setup automated daily backups
sudo crontab -e

# Add this line for daily backup at 2 AM
0 2 * * * /opt/zain-hms/scripts/zain-hms-maintenance.sh backup-auto
```

#### Manual Backup

```bash
# Create immediate backup
sudo /opt/zain-hms/scripts/zain-hms-maintenance.sh
# Select: Backup & Restore → Create Backup
```

#### Restore from Backup

```bash
# Restore from specific backup
sudo /opt/zain-hms/scripts/zain-hms-maintenance.sh
# Select: Backup & Restore → Restore Backup
```

### Updates

#### Automatic Updates

```bash
# Setup automatic updates
sudo /opt/zain-hms/scripts/setup-auto-updates.sh
```

#### Manual Updates

```bash
# Update ZAIN HMS
sudo /opt/zain-hms/scripts/zain-hms-maintenance.sh
# Select: System Management → Update ZAIN HMS
```

## 🔒 Security

### Security Checklist

#### Essential Security Steps

1. **Change Default Passwords**
   ```bash
   # Change admin password via web interface
   # Change database passwords via maintenance tool
   ```

2. **Configure Firewall**
   ```bash
   sudo ufw enable
   sudo ufw default deny incoming
   sudo ufw allow ssh
   sudo ufw allow http
   sudo ufw allow https
   ```

3. **Setup SSL Certificate**
   ```bash
   sudo /opt/zain-hms/scripts/setup-ssl.sh yourdomain.com
   ```

4. **Enable Fail2Ban**
   ```bash
   sudo apt install fail2ban
   sudo systemctl enable fail2ban
   sudo systemctl start fail2ban
   ```

5. **Regular Security Updates**
   ```bash
   sudo /opt/zain-hms/scripts/security-updates.sh
   ```

#### Security Monitoring

```bash
# View security logs
sudo tail -f /opt/zain-hms/logs/security.log

# Run security audit
sudo /opt/zain-hms/scripts/zain-hms-maintenance.sh
# Select: Security & Monitoring → Security Audit
```

#### Data Protection

- Database encryption at rest
- SSL/TLS for data in transit
- Regular security backups
- Access logging and monitoring
- User permission management

### Compliance Features

ZAIN HMS includes features for healthcare compliance:
- HIPAA compliance tools
- Audit trails
- Data encryption
- Access controls
- Privacy protection
- Secure patient data handling

## 📞 Support and Resources

### Getting Help

1. **Documentation**: 
   - Online: `https://github.com/mehedi-hossain95/zain_hms/wiki`
   - Local: `/opt/zain-hms/docs/`

2. **Issue Reporting**:
   - GitHub Issues: `https://github.com/mehedi-hossain95/zain_hms/issues`
   - Bug reports and feature requests

3. **Community Support**:
   - Discussions: `https://github.com/mehedi-hossain95/zain_hms/discussions`
   - Community forums and help

4. **Professional Support**:
   - Email: `support@zainhms.com`
   - Commercial support available

### Useful Commands

```bash
# Quick status check
sudo systemctl status zain-hms

# View all logs
sudo journalctl -u zain-hms -f

# Restart all services
sudo systemctl restart zain-hms

# Access maintenance menu
sudo /opt/zain-hms/scripts/zain-hms-maintenance.sh

# Check system health
curl http://localhost/health/

# View Docker containers
sudo docker ps

# Access database
sudo docker-compose -f /opt/zain-hms/docker-compose.prod.yml exec db psql -U zain_hms
```

## 📋 Installation Checklist

Use this checklist to ensure proper installation:

### Pre-Installation
- [ ] System meets minimum requirements
- [ ] Server has internet access (for online installation)
- [ ] Root/sudo access available
- [ ] Firewall configured to allow HTTP/HTTPS
- [ ] Domain name configured (if using custom domain)

### During Installation
- [ ] Installation script completes successfully
- [ ] All Docker containers start properly
- [ ] Database migrations complete
- [ ] Web interface accessible
- [ ] No error messages in logs

### Post-Installation
- [ ] Admin password changed from default
- [ ] System settings configured
- [ ] User accounts created
- [ ] SSL certificate installed (for production)
- [ ] Firewall properly configured
- [ ] Backup system configured
- [ ] Monitoring setup complete

### Production Readiness
- [ ] Performance tuning applied
- [ ] Security audit completed
- [ ] Compliance requirements met
- [ ] Staff training completed
- [ ] Documentation reviewed
- [ ] Support contacts established

---

## 🎉 Conclusion

Congratulations! You now have a comprehensive guide for installing and managing ZAIN HMS as downloadable software. This system provides:

- **Easy Installation**: Multiple installation methods for different needs
- **Complete Management**: Comprehensive maintenance and update tools
- **Enterprise Ready**: Offline installation and professional features
- **Secure by Default**: Built-in security features and compliance tools
- **Community Supported**: Active development and community support

**May Allah bless this installation and make it beneficial for healthcare services worldwide. Ameen.**

---

*For updates and latest documentation, visit our GitHub repository at `https://github.com/mehedi-hossain95/zain_hms`*