# 🔐 GitHub Repository Secrets Configuration Guide

This document lists all the secrets that need to be configured in your GitHub repository for the CI/CD pipeline to work properly.

## 🚀 How to Add Secrets to GitHub Repository

1. Go to your GitHub repository: `https://github.com/Zain-Technologies-22/ZAIN-HMS`
2. Click on **Settings** tab
3. In the left sidebar, click **Secrets and variables** → **Actions**
4. Click **New repository secret** for each secret below

## 📋 Required Repository Secrets

### 🖥️ Server Connection Secrets

**PRODUCTION_SERVER_IP**
- **Value**: Your Ubuntu server IP address (e.g., `192.168.1.100`)
- **Description**: IP address of your production server

**PRODUCTION_SERVER_USER**
- **Value**: SSH username for server access (e.g., `root` or `ubuntu`)
- **Description**: Username for SSH connection to production server

**PRODUCTION_SSH_KEY**
- **Value**: Private SSH key content (entire key including `-----BEGIN` and `-----END` lines)
- **Description**: SSH private key for passwordless access to production server
- **Generation**: 
  ```bash
  ssh-keygen -t ed25519 -C "github-actions@zainhms.com"
  # Add public key to server: ~/.ssh/authorized_keys
  # Copy private key content to this secret
  ```

### 🗄️ Database Secrets

**DB_NAME**
- **Value**: `zain_hms`
- **Description**: Production database name

**DB_USER**
- **Value**: `zain_hms_user`
- **Description**: Database username

**DB_PASSWORD**
- **Value**: Strong, unique password (e.g., `ZH_db_2024_SecurePwd#123`)
- **Description**: Database password (minimum 16 characters)

### 🔑 Application Secrets

**SECRET_KEY**
- **Value**: 50+ character Django secret key
- **Description**: Django SECRET_KEY for production
- **Generation**: 
  ```python
  from django.core.management.utils import get_random_secret_key
  print(get_random_secret_key())
  ```

**ALLOWED_HOSTS**
- **Value**: `yourdomain.com,www.yourdomain.com,your-server-ip`
- **Description**: Comma-separated list of allowed hosts

**MAIN_DOMAIN**
- **Value**: `yourdomain.com`
- **Description**: Main domain for the application

### 📧 Email Configuration

**EMAIL_HOST**
- **Value**: `smtp.gmail.com` (or your email provider's SMTP)
- **Description**: SMTP server for sending emails

**EMAIL_HOST_USER**
- **Value**: `your-email@gmail.com`
- **Description**: Email username for SMTP authentication

**EMAIL_HOST_PASSWORD**
- **Value**: App-specific password or email password
- **Description**: Email password for SMTP authentication
- **Note**: For Gmail, use App Passwords instead of regular password

### ☁️ AWS Configuration (Optional)

**AWS_ACCESS_KEY_ID**
- **Value**: Your AWS access key ID
- **Description**: AWS access key for S3 media storage

**AWS_SECRET_ACCESS_KEY**
- **Value**: Your AWS secret access key
- **Description**: AWS secret key for S3 media storage

**AWS_STORAGE_BUCKET_NAME**
- **Value**: `zain-hms-production-media`
- **Description**: S3 bucket name for media files

### 🔔 Notification Secrets (Optional)

**SLACK_WEBHOOK_URL**
- **Value**: Slack webhook URL for deployment notifications
- **Description**: Webhook URL for Slack notifications
- **Setup**: Create webhook in Slack → Apps → Incoming Webhooks

### 🔒 Redis Configuration

**REDIS_PASSWORD**
- **Value**: Strong Redis password (e.g., `Redis_ZH_2024_Secure#456`)
- **Description**: Password for Redis cache authentication

## 🔧 Environment-Specific Secrets

### Production Environment

These secrets are used when deploying to the `production` branch:

```bash
# Server Configuration
PRODUCTION_SERVER_IP=your.server.ip.address
PRODUCTION_SERVER_USER=root
PRODUCTION_SSH_KEY=-----BEGIN OPENSSH PRIVATE KEY-----...

# Database Configuration  
DB_NAME=zain_hms
DB_USER=zain_hms_user
DB_PASSWORD=your-production-db-password

# Application Configuration
SECRET_KEY=your-50-character-production-secret-key
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,server-ip
MAIN_DOMAIN=yourdomain.com

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=production@yourdomain.com
EMAIL_HOST_PASSWORD=your-email-app-password

# Cache Configuration
REDIS_PASSWORD=your-redis-password
```

## 🛠️ Quick Setup Script

You can use this script to generate some of the required secrets:

```bash
#!/bin/bash
# Generate secrets for ZAIN HMS

echo "🔐 ZAIN HMS Secrets Generator"
echo "============================"

# Generate Django SECRET_KEY
echo ""
echo "Django SECRET_KEY:"
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Generate strong passwords
echo ""
echo "Database Password:"
openssl rand -base64 32

echo ""
echo "Redis Password:"
openssl rand -base64 24

# Generate SSH key pair
echo ""
echo "Generating SSH key pair for deployment..."
ssh-keygen -t ed25519 -f ./deployment_key -C "github-actions@zainhms.com" -N ""
echo "Public key (add to server ~/.ssh/authorized_keys):"
cat deployment_key.pub
echo ""
echo "Private key (add to GitHub PRODUCTION_SSH_KEY secret):"
cat deployment_key
rm deployment_key deployment_key.pub
```

## ✅ Validation Checklist

Before enabling automatic deployment, ensure:

- [ ] **Server Access**: SSH connection works with the provided key
- [ ] **Domain Configuration**: DNS points to your server IP
- [ ] **Email Configuration**: SMTP settings are correct and tested
- [ ] **Database Access**: Database credentials are valid
- [ ] **SSL Certificate**: Let's Encrypt or custom SSL is configured
- [ ] **Firewall Rules**: Ports 80, 443, and SSH are properly configured
- [ ] **Backup Strategy**: Database backup system is in place
- [ ] **Monitoring**: Basic monitoring and alerting is configured

## 🚨 Security Best Practices

1. **Use strong, unique passwords** for all services
2. **Enable 2FA** on all accounts (GitHub, AWS, email)
3. **Rotate secrets regularly** (at least every 90 days)
4. **Use separate credentials** for production and staging
5. **Monitor access logs** for unusual activity
6. **Keep SSH keys secure** and rotate them periodically
7. **Use app-specific passwords** for email services
8. **Enable audit logging** in all services

## 🔄 Secret Rotation Schedule

| Secret Type | Rotation Frequency | Last Rotated | Next Rotation |
|-------------|-------------------|--------------|---------------|
| SSH Keys | Every 6 months | - | - |
| Database Passwords | Every 3 months | - | - |
| Django SECRET_KEY | Every 12 months | - | - |
| API Keys | Every 6 months | - | - |
| Email Passwords | Every 3 months | - | - |

## 🆘 Emergency Access

In case of emergency:
1. **Server Access**: Use console access through hosting provider
2. **Database Recovery**: Use the automated backup system
3. **Application Recovery**: Deploy from previous stable release
4. **Communication**: Use emergency contact list

## 📞 Support Contacts

- **System Administrator**: admin@yourdomain.com
- **DevOps Team**: devops@yourdomain.com
- **Emergency Hotline**: +1-XXX-XXX-XXXX