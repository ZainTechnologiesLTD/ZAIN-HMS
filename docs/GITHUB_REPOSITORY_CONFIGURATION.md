# 🛡️ ZAIN HMS GitHub Repository Configuration

This document outlines the recommended repository settings for ZAIN HMS to ensure secure, automated development workflows.

## 🔒 Branch Protection Rules

### Main Branch Protection

Configure the following settings for the `main` branch:

#### Required Status Checks
- ✅ **Require status checks to pass before merging**
- ✅ **Require branches to be up to date before merging**

**Required checks:**
- `security-scan`
- `django-tests`
- `frontend-build` 
- `comprehensive-tests`
- `migration-tests`
- `deployment-preview`

#### Pull Request Requirements
- ✅ **Require pull request reviews before merging**
- **Required approving reviews:** 1
- ✅ **Dismiss stale PR reviews when new commits are pushed**
- ✅ **Require review from code owners**
- ✅ **Restrict pushes that create files**

#### Additional Restrictions
- ✅ **Restrict pushes to matching branches**
- ✅ **Allow force pushes** ❌ (Disabled for security)
- ✅ **Allow deletions** ❌ (Disabled for security)

### Development Branch Protection

Configure the following settings for the `development` branch:

#### Required Status Checks
- ✅ **Require status checks to pass before merging**

**Required checks:**
- `security-scan`
- `django-tests`
- `frontend-build`

#### Pull Request Requirements
- ✅ **Require pull request reviews before merging**
- **Required approving reviews:** 1

## 🏷️ Repository Settings

### General Settings
- **Repository name:** `zain_hms`
- **Description:** `ZAIN Hospital Management System - Comprehensive healthcare management solution with Django`
- **Website:** `https://zainhms.com`
- **Topics:** `healthcare`, `hospital-management`, `django`, `python`, `medical`, `hms`

### Features
- ✅ **Issues**
- ✅ **Projects** 
- ✅ **Wiki** ❌ (Use docs/ directory instead)
- ✅ **Discussions**
- ✅ **Sponsors**

### Pull Requests
- ✅ **Allow merge commits**
- ✅ **Allow squash merging** (Recommended)
- ✅ **Allow rebase merging**
- ✅ **Always suggest updating pull request branches**
- ✅ **Allow auto-merge**
- ✅ **Automatically delete head branches**

### Security
- ✅ **Enable vulnerability alerts**
- ✅ **Enable Dependabot security updates**
- ✅ **Enable Dependabot version updates**

## 🔑 Required Repository Secrets

Configure the following secrets in **Settings → Secrets and variables → Actions**:

### Production Secrets
```
PROD_SECRET_KEY          # Django secret key for production (50+ characters)
PROD_DATABASE_URL        # Production database connection string
PROD_REDIS_URL           # Production Redis connection string
PROD_ALLOWED_HOSTS       # Comma-separated list of allowed hosts
PROD_SENTRY_DSN          # Sentry error tracking DSN (optional)
```

### Deployment Secrets  
```
PROD_SSH_PRIVATE_KEY     # SSH private key for production server
PROD_SERVER_HOST         # Production server hostname/IP
PROD_SERVER_USER         # Production server username
STAGING_SSH_PRIVATE_KEY  # SSH private key for staging server
STAGING_SERVER_HOST      # Staging server hostname/IP  
STAGING_SERVER_USER      # Staging server username
```

### Third-party Integrations
```
SLACK_WEBHOOK_URL        # Slack notifications webhook
EMAIL_SMTP_PASSWORD      # Email service password
BACKUP_S3_ACCESS_KEY     # AWS S3 backup access key
BACKUP_S3_SECRET_KEY     # AWS S3 backup secret key
```

## 📋 Environment Variables

Configure the following environment variables:

### Staging Environment
```
ENVIRONMENT=staging
DEBUG=False
ALLOWED_HOSTS=staging.zainhms.com
DATABASE_URL=postgresql://user:pass@staging-db:5432/zain_hms_staging
REDIS_URL=redis://staging-redis:6379/0
```

### Production Environment  
```
ENVIRONMENT=production
DEBUG=False
ALLOWED_HOSTS=zainhms.com,www.zainhms.com
DATABASE_URL=postgresql://user:pass@prod-db:5432/zain_hms_production
REDIS_URL=redis://prod-redis:6379/0
```

## 🤖 Automated Workflows

The repository includes the following automated workflows:

### 1. Development CI/CD (`ci-development.yml`)
- **Trigger:** Push to `development` branch
- **Actions:** Security scan, Django tests, frontend build, performance tests, dev deployment

### 2. Pull Request Automation (`pr-automation.yml`)  
- **Trigger:** Pull requests to `main` branch
- **Actions:** PR validation, comprehensive tests, migration tests, deployment preview

### 3. Production Deployment (`production-deployment.yml`)
- **Trigger:** Push to `main` branch or release published
- **Actions:** Pre-deployment validation, staging deployment, production deployment, monitoring

### 4. Release Management (`release-management.yml`)
- **Trigger:** Push to `main` branch or manual workflow dispatch
- **Actions:** Semantic versioning, changelog generation, GitHub release, documentation update

## 🔄 Development Workflow

### Modern Git Workflow Process:

1. **Feature Development**
   ```bash
   # Create feature branch from development
   git checkout development
   git pull origin development  
   git checkout -b feature/patient-search-enhancement
   
   # Develop and commit changes
   git add .
   git commit -m "feat(patients): add advanced search with filters"
   
   # Push feature branch
   git push origin feature/patient-search-enhancement
   ```

2. **Create Pull Request to Development**
   - Open PR from `feature/patient-search-enhancement` → `development`
   - Automated CI/CD runs (security, tests, build)
   - Code review and approval
   - Merge to development branch

3. **Development to Main (Release)**
   ```bash
   # Create release PR from development to main
   git checkout development
   git pull origin development
   git checkout -b release/v2.1.0
   git push origin release/v2.1.0
   ```
   
   - Open PR from `release/v2.1.0` → `main`
   - Comprehensive testing and validation
   - Staging deployment preview
   - Code review and approval
   - Merge to main branch

4. **Automated Production Release**
   - Push to main triggers release management
   - Semantic versioning and changelog
   - GitHub release created
   - Production deployment initiated

## 📊 Monitoring and Alerts

### Required Monitoring Setup:
- **Health Check Endpoints:** `/health/`, `/api/health/`
- **Error Tracking:** Sentry integration
- **Performance Monitoring:** Database query optimization
- **Security Monitoring:** Failed login attempts, suspicious activity
- **Uptime Monitoring:** External service monitoring

### Alert Configuration:
- **Error Rate:** > 5% for 5 minutes
- **Response Time:** > 2 seconds for 5 minutes  
- **Database:** Connection failures or high query time
- **Disk Space:** > 85% usage
- **Memory:** > 90% usage

## 🛡️ Security Best Practices

### Code Security:
- Automated security scanning with Bandit
- Dependency vulnerability scanning with Safety
- SAST (Static Application Security Testing)
- Branch protection rules enforced

### Infrastructure Security:
- SSH key-based authentication
- Encrypted secrets storage
- HTTPS-only communication
- Regular security updates

### Compliance:
- HIPAA compliance for healthcare data
- Regular security audits
- Access logging and monitoring
- Data backup and recovery procedures

## 📚 Additional Resources

- [Production Deployment Checklist](./PRODUCTION_CHECKLIST.md)
- [Auto-Upgrade System Guide](./AUTO_UPGRADE_SYSTEM.md) 
- [Security Configuration](./SECURITY_CONFIGURATION.md)
- [Performance Optimization](./PERFORMANCE_OPTIMIZATION.md)

---

**Note:** This configuration ensures a secure, automated, and efficient development workflow for ZAIN HMS. Adjust settings based on your specific requirements and security policies.