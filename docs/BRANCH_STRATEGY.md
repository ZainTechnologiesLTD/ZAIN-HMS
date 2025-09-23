# ZAIN HMS Branch Strategy & Client Update System

## 📋 **Branch Strategy Overview**

### **Branch Structure**
```
main (production) ← Clients get updates from here
├── development ← Active development & testing
└── feature/* ← Individual feature development
```

## 🔄 **How Client Updates Work**

### **Production Release Workflow**

1. **Development Phase** → Work happens on `development` branch
2. **Testing & QA** → All features tested on `development`
3. **Release Creation** → Create tag (e.g., `v2.1.0`) on `development`
4. **GitHub Actions** → Automatically merges `development` → `main`
5. **Client Notification** → Hospital admins get in-app update notifications

### **Client Update Sources**

| Environment | Branch | Purpose | Auto-Updates |
|-------------|---------|---------|--------------|
| **Production Hospitals** | `main` | Stable releases only | ✅ Yes |
| **Testing Hospitals** | `development` | Latest features | ⚠️ Optional |
| **Demo/Preview** | `staging` | Pre-production testing | 🔄 Manual |

## 🏥 **For Hospital IT Administrators**

### **Production Clients Should Use:**
- **Branch**: `main` 
- **Update Source**: GitHub Releases (tagged versions)
- **Frequency**: When stable releases are available
- **Safety**: Full migration validation, rollback support

### **Update Process for Hospitals:**
1. **Notification**: In-app notification appears for admin users
2. **Review**: Check changelog and release notes
3. **Maintenance Mode**: System automatically enables maintenance mode
4. **Migration Validation**: Database changes validated before applying
5. **Update**: Zero-downtime deployment with automatic backup
6. **Verification**: Health checks ensure system is working
7. **Completion**: Maintenance mode disabled, users notified

## 🚀 **Current Setup Status**

### ✅ **Completed Infrastructure:**
- Update notification system
- Automatic migration validation
- Zero-downtime deployment
- Rollback capabilities
- Production-ready CI/CD pipeline

### 🔧 **Branch Configuration:**
```python
# From zain_hms/version.py
PRODUCTION_BRANCH = "main"        # ← Clients get updates from here
DEVELOPMENT_BRANCH = "development" # ← Development work happens here
UPDATE_CHECK_BRANCH = "main"      # ← API checks this branch for releases
```

## 📱 **In-App Update Notifications**

Hospital admins will see:
- 🔔 **New Version Available**: Clear notification in dashboard
- 📋 **Release Notes**: What's new and improved
- 🛡️ **Safety Info**: Migration details, expected downtime
- 🎯 **One-Click Update**: Simple update process with progress tracking

## 🎯 **Answer to Your Question**

**"So client get update/upgrade from which branch?"**

✅ **Answer: Clients get updates from the `main` branch**

- **Development work** happens on `development` branch
- **Stable releases** are merged to `main` branch via GitHub Actions
- **Hospital clients** download/update from `main` branch only
- **Update checks** look for GitHub releases tagged from `main` branch

## 🔄 **Next Steps**

1. **Create First Production Release**:
   ```bash
   # Tag current development for production release
   git tag v2.1.0
   git push origin v2.1.0
   ```

2. **GitHub Actions Will**:
   - Merge `development` → `main`
   - Create GitHub Release
   - Trigger client update notifications

3. **Hospital Clients Will**:
   - Receive in-app update notification
   - Download update from `main` branch
   - Apply with zero-downtime deployment

Would you like me to create the first production release now?