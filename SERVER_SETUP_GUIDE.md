# ZAIN HMS - Server Environment Setup Guide

## 🖥️ **Server Requirements**

### **Minimum Specifications**
- **OS**: Ubuntu 20.04 LTS or 22.04 LTS
- **CPU**: 4 cores (Intel/AMD x64)
- **RAM**: 8GB (16GB recommended)
- **Storage**: 100GB SSD (500GB+ recommended)
- **Network**: 100Mbps internet connection
- **Domain**: Registered domain name with DNS control

### **Recommended Specifications (Hospital Production)**
- **CPU**: 8+ cores (Intel Xeon or AMD EPYC)
- **RAM**: 32GB+ (for multiple concurrent users)
- **Storage**: 1TB+ NVMe SSD with backup drives
- **Network**: 1Gbps+ with redundancy
- **Backup**: Daily automated backups to cloud storage

## 🚀 **Quick Setup Instructions**

### **Step 1: Server Preparation**
```bash
# 1. Get a fresh Ubuntu server (DigitalOcean, AWS, etc.)
# 2. Point your domain to the server IP
# 3. SSH into the server as root

# Update system
apt update && apt upgrade -y
```

### **Step 2: Download & Run Setup**
```bash
# Download the setup script
wget https://raw.githubusercontent.com/Zain-Technologies-22/ZAIN-HMS/main/scripts/setup_server.sh

# Make it executable
chmod +x setup_server.sh

# Run the setup (replace with your domain)
sudo ./setup_server.sh your-domain.com
```

### **Step 3: Deploy ZAIN HMS**
```bash
# Download deployment script
wget https://raw.githubusercontent.com/Zain-Technologies-22/ZAIN-HMS/main/scripts/deploy_to_server.sh

# Run deployment
chmod +x deploy_to_server.sh
sudo ./deploy_to_server.sh
```

## 🔧 **Manual Setup Process**

If you prefer step-by-step manual setup:

### **1. System Packages**
```bash
apt install -y python3 python3-pip python3-venv postgresql redis-server nginx certbot supervisor
```

### **2. Database Setup**
```bash
sudo -u postgres createuser zain_hms
sudo -u postgres createdb zain_hms_db
sudo -u postgres psql -c "ALTER USER zain_hms PASSWORD 'secure_password';"
```

### **3. Application Deployment**
```bash
cd /var/www
git clone https://github.com/Zain-Technologies-22/ZAIN-HMS.git zain_hms
cd zain_hms
python3 -m venv venv
source venv/bin/activate
pip install -r requirements_production.txt
```

### **4. Environment Configuration**
Create `.env` file with:
```env
DEBUG=False
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://zain_hms:password@localhost/zain_hms_db
REDIS_URL=redis://localhost:6379/1
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
```

### **5. Database Migration**
```bash
python manage.py migrate --settings=zain_hms.production_settings
python manage.py collectstatic --noinput --settings=zain_hms.production_settings
python manage.py createsuperuser --settings=zain_hms.production_settings
```

## 🔐 **Security Configuration**

### **Firewall Setup**
```bash
ufw enable
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 'Nginx Full'
```

### **SSL Certificate**
```bash
certbot --nginx -d your-domain.com -d www.your-domain.com
```

### **Database Security**
- Use strong passwords (32+ characters)
- Restrict database access to localhost only
- Enable PostgreSQL logging
- Regular security updates

## 📊 **Performance Optimization**

### **Database Tuning**
```sql
-- PostgreSQL configuration
shared_buffers = 256MB
effective_cache_size = 1GB
max_connections = 200
```

### **Redis Configuration**
```conf
maxmemory 256mb
maxmemory-policy allkeys-lru
```

### **Nginx Optimization**
```nginx
worker_processes auto;
client_max_body_size 100M;
gzip on;
gzip_types text/css application/javascript image/svg+xml;
```

## 💾 **Backup Strategy**

### **Automated Daily Backups**
```bash
# Database backup
pg_dump zain_hms_db > backup_$(date +%Y%m%d).sql

# Media files backup
tar -czf media_backup_$(date +%Y%m%d).tar.gz /var/www/zain_hms/media/

# Configuration backup
cp -r /var/www/zain_hms/.env /backup/
```

### **Cloud Backup Integration**
- AWS S3 for media files
- Automated database dumps to cloud storage
- Configuration management with version control

## 📈 **Monitoring & Maintenance**

### **Log Files**
- Application: `/var/log/zain_hms/application.log`
- Nginx: `/var/log/nginx/access.log`
- PostgreSQL: `/var/log/postgresql/`
- System: `/var/log/syslog`

### **Health Monitoring**
```bash
# Check services
systemctl status nginx postgresql redis supervisor

# View application logs
tail -f /var/log/zain_hms/application.log

# Monitor system resources
htop
df -h
free -h
```

### **Update Process**
```bash
# Update ZAIN HMS
cd /var/www/zain_hms
git pull origin main
pip install -r requirements_production.txt
python manage.py migrate --settings=zain_hms.production_settings
supervisorctl restart zain_hms
```

## 🌐 **Multi-Hospital Setup**

### **Shared Server Architecture**
- Use Docker containers for isolation
- Separate databases per hospital
- Shared Redis for caching
- Load balancer for high availability

### **Docker Deployment**
```bash
# Use provided docker-compose.yml
docker-compose up -d --scale web=3
```

## 🆘 **Troubleshooting**

### **Common Issues**

**1. Application Won't Start**
```bash
# Check logs
tail -f /var/log/zain_hms/application.log
supervisorctl status
```

**2. Database Connection Errors**
```bash
# Test database connection
sudo -u postgres psql zain_hms_db -c "SELECT version();"
```

**3. Static Files Not Loading**
```bash
# Recollect static files
python manage.py collectstatic --noinput --settings=zain_hms.production_settings
```

**4. SSL Certificate Issues**
```bash
# Renew certificate
certbot renew --dry-run
```

### **Emergency Recovery**
```bash
# Restore from backup
pg_restore -d zain_hms_db backup_file.sql
tar -xzf media_backup.tar.gz -C /var/www/zain_hms/
supervisorctl restart zain_hms
```

## 📞 **Support Information**

### **Server Specifications Verification**
```bash
# System information
lscpu
free -h
df -h
uname -a
```

### **Performance Benchmarking**
```bash
# Database performance
pgbench -i -s 10 zain_hms_db
pgbench -c 10 -j 2 -t 1000 zain_hms_db
```

## ✅ **Post-Deployment Checklist**

- [ ] Domain pointing to server IP
- [ ] SSL certificate installed and working
- [ ] Database migrations completed
- [ ] Superuser account created
- [ ] Static files served correctly
- [ ] Media upload working
- [ ] Email configuration tested
- [ ] Backup system operational
- [ ] Monitoring alerts configured
- [ ] Security firewall active
- [ ] Performance optimization applied

---

**🏥 Your ZAIN HMS production server is now ready for hospital operations!**

For support, please check the logs first, then refer to the troubleshooting section above.