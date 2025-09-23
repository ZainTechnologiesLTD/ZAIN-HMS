# ZAIN HMS Production Deployment Checklist

## 🚀 **Pre-Deployment Checklist**

### **1. Server Environment Setup**
- [ ] **Server Requirements**
  - Ubuntu 20.04+ or CentOS 8+
  - Python 3.8+ installed
  - Nginx or Apache web server
  - SSL certificate installed
  - Minimum 2GB RAM, 20GB disk space

- [ ] **System Dependencies**
  ```bash
  sudo apt update
  sudo apt install python3-pip python3-venv nginx redis-server
  sudo systemctl enable redis-server nginx
  ```

### **2. Environment Configuration**
- [ ] **Create Production Environment File**
  ```bash
  cp .env.production.template .env.production
  ```

- [ ] **Required Environment Variables**
  ```bash
  # Critical - Must be set
  ENVIRONMENT=production
  DEBUG=False
  SECRET_KEY=your-50-character-secret-key
  ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
  
  # Database (if using PostgreSQL)
  DB_NAME=zain_hms_prod
  DB_USER=zain_hms_user
  DB_PASSWORD=secure-password
  DB_HOST=localhost
  
  # Redis Cache
  REDIS_CACHE_URL=redis://127.0.0.1:6379/1
  
  # SSL/Security
  SECURE_SSL_REDIRECT=True
  SECURE_HSTS_SECONDS=31536000
  
  # Email Configuration
  EMAIL_HOST=smtp.your-provider.com
  EMAIL_HOST_USER=your-email@domain.com
  EMAIL_HOST_PASSWORD=your-password
  ```

### **3. Database Setup**

#### **Option A: SQLite (Default)**
- [ ] Ensure SQLite is installed
- [ ] Database will be created automatically

#### **Option B: PostgreSQL (Recommended for Production)**
- [ ] Install PostgreSQL
  ```bash
  sudo apt install postgresql postgresql-contrib
  ```
- [ ] Create database and user
  ```sql
  CREATE DATABASE zain_hms_prod;
  CREATE USER zain_hms_user WITH PASSWORD 'secure-password';
  GRANT ALL PRIVILEGES ON DATABASE zain_hms_prod TO zain_hms_user;
  ```
- [ ] Update DATABASES in .env.production

#### **Option C: MySQL/MariaDB**
- [ ] Install MySQL/MariaDB
- [ ] Create database and user
- [ ] Install mysql client: `pip install mysqlclient`

### **4. Security Configuration**
- [ ] **SSL Certificate**
  - Obtain SSL certificate (Let's Encrypt recommended)
  - Configure Nginx/Apache for HTTPS
  - Test HTTPS redirect

- [ ] **Firewall Setup**
  ```bash
  sudo ufw enable
  sudo ufw allow 22/tcp
  sudo ufw allow 80/tcp
  sudo ufw allow 443/tcp
  ```

- [ ] **File Permissions**
  ```bash
  chmod 644 .env.production
  chmod 755 deploy_unified.sh
  chown -R www-data:www-data /path/to/zain_hms/
  ```

### **5. Application Setup**
- [ ] **Clone Repository**
  ```bash
  git clone <your-repo-url> /var/www/zain_hms
  cd /var/www/zain_hms
  ```

- [ ] **Install Dependencies**
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
  ```

- [ ] **Configure Static Files Directory**
  ```bash
  mkdir -p /var/www/zain_hms/staticfiles
  mkdir -p /var/www/zain_hms/media
  chown -R www-data:www-data /var/www/zain_hms/
  ```

### **6. Web Server Configuration**

#### **Nginx Configuration** (Recommended)
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/private.key;
    
    # Security headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    location /static/ {
        alias /var/www/zain_hms/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    location /media/ {
        alias /var/www/zain_hms/media/;
    }
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### **7. Process Management**

#### **Systemd Service Configuration**
Create `/etc/systemd/system/zain-hms.service`:
```ini
[Unit]
Description=ZAIN HMS Django Application
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/zain_hms
Environment=ENVIRONMENT=production
EnvironmentFile=/var/www/zain_hms/.env.production
ExecStart=/var/www/zain_hms/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 zain_hms.wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable zain-hms
sudo systemctl start zain-hms
```

### **8. Deployment Process**
- [ ] **Set Environment**
  ```bash
  export ENVIRONMENT=production
  ```

- [ ] **Run Deployment Script**
  ```bash
  cd /var/www/zain_hms
  ./deploy_unified.sh
  ```

- [ ] **Create Superuser**
  ```bash
  python manage.py createsuperuser
  ```

### **9. Auto-Upgrade System Setup**
- [ ] **Install Auto-Upgrade Dependencies**
  ```bash
  pip install gitpython schedule
  ```

- [ ] **Configure Auto-Upgrade Service** (Coming in next phase)
- [ ] **Set Backup Strategy**
- [ ] **Configure Rollback Mechanism**

### **10. Post-Deployment Verification**
- [ ] **Health Checks**
  - [ ] Website loads correctly (https://yourdomain.com)
  - [ ] Admin panel accessible (/admin/)
  - [ ] Static files loading
  - [ ] Database connections working
  - [ ] Email notifications working
  - [ ] SSL certificate valid

- [ ] **Performance Tests**
  - [ ] Page load times < 3 seconds
  - [ ] Redis cache working
  - [ ] File uploads working
  - [ ] Login/logout functionality

- [ ] **Security Tests**
  - [ ] HTTPS redirect working
  - [ ] Security headers present
  - [ ] Admin URL secure
  - [ ] File permissions correct

### **11. Monitoring Setup**
- [ ] **Log Monitoring**
  - Configure log rotation
  - Set up error alerting
  - Monitor authentication.log and security.log

- [ ] **Server Monitoring**
  - CPU and memory usage
  - Disk space monitoring
  - Database performance

- [ ] **Application Monitoring**
  - Error tracking (Sentry recommended)
  - Performance monitoring
  - Uptime monitoring

### **12. Backup Strategy**
- [ ] **Automated Database Backups**
  ```bash
  # Add to crontab
  0 2 * * * cd /var/www/zain_hms && python manage.py dbbackup
  ```

- [ ] **File Backups**
  - Media files backup
  - Configuration files backup
  - Complete system backup

### **🚨 Emergency Procedures**
- [ ] **Rollback Plan**
  - Database restore procedure
  - Application rollback steps
  - Configuration restore

- [ ] **Disaster Recovery**
  - Full system restore procedure
  - Data recovery contacts
  - Alternative hosting setup

### **📞 Support Contacts**
- System Administrator: [contact info]
- Database Administrator: [contact info]
- Security Team: [contact info]
- Hosting Provider: [contact info]

---

**✅ Deployment Complete!**

Once all checkboxes are marked, your ZAIN HMS production deployment is ready for healthcare operations with enterprise-grade security and performance.