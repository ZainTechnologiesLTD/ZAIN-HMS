# ZAIN HMS Auto-Upgrade System Configuration

## 🔄 **Auto-Upgrade System Components**

### **1. Auto-Upgrade Script**
- **Location**: `scripts/auto_upgrade.py`
- **Purpose**: Safely manages automated updates with rollback capability
- **Features**:
  - Git-based update detection
  - Pre/post upgrade health checks
  - Automatic backup and rollback
  - Service restart management
  - Comprehensive logging

### **2. Installation & Setup**

#### **Install Dependencies**
```bash
# Install GitPython for git operations
pip install GitPython schedule

# Make script executable
chmod +x scripts/auto_upgrade.py
```

#### **Create Auto-Upgrade Service**
Create `/etc/systemd/system/zain-hms-autoupgrade.service`:
```ini
[Unit]
Description=ZAIN HMS Auto-Upgrade Service
After=network.target

[Service]
Type=oneshot
User=www-data
WorkingDirectory=/var/www/zain_hms
Environment=ENVIRONMENT=production
EnvironmentFile=/var/www/zain_hms/.env.production
ExecStart=/var/www/zain_hms/venv/bin/python /var/www/zain_hms/scripts/auto_upgrade.py
StandardOutput=journal
StandardError=journal
```

#### **Create Auto-Upgrade Timer**
Create `/etc/systemd/system/zain-hms-autoupgrade.timer`:
```ini
[Unit]
Description=ZAIN HMS Auto-Upgrade Timer
Requires=zain-hms-autoupgrade.service

[Timer]
# Run every day at 2 AM
OnCalendar=*-*-* 02:00:00
# Run 5 minutes after boot if missed
OnBootSec=5min
# Randomize start time by up to 30 minutes
RandomizedDelaySec=30min
Persistent=true

[Install]
WantedBy=timers.target
```

#### **Enable Auto-Upgrade Timer**
```bash
sudo systemctl daemon-reload
sudo systemctl enable zain-hms-autoupgrade.timer
sudo systemctl start zain-hms-autoupgrade.timer

# Check timer status
sudo systemctl status zain-hms-autoupgrade.timer
sudo systemctl list-timers zain-hms-autoupgrade.timer
```

### **3. Manual Usage**

#### **Check for Updates Only**
```bash
cd /var/www/zain_hms
python scripts/auto_upgrade.py --check-only
```

#### **Force Upgrade (Even if No Updates)**
```bash
python scripts/auto_upgrade.py --force
```

#### **Run Normal Upgrade Check**
```bash
python scripts/auto_upgrade.py
```

### **4. Configuration Options**

#### **Environment Variables** (add to `.env.production`)
```bash
# Auto-upgrade settings
AUTO_UPGRADE_ENABLED=true
AUTO_UPGRADE_BRANCH=main
AUTO_UPGRADE_TIME=02:00
AUTO_UPGRADE_BACKUP_RETENTION=30  # days

# Notification settings
AUTO_UPGRADE_NOTIFY_EMAIL=admin@yourdomain.com
AUTO_UPGRADE_SLACK_WEBHOOK=https://hooks.slack.com/...
```

### **5. Safety Features**

#### **Pre-Upgrade Checks**
- ✅ Environment verification (production mode)
- ✅ Disk space check (minimum 1GB free)
- ✅ Database connectivity test
- ✅ Redis connectivity test (if configured)
- ✅ Backup directory write permissions

#### **Post-Upgrade Tests**
- ✅ Django system check
- ✅ Database query functionality
- ✅ Static files integrity
- ✅ Application import tests

#### **Automatic Rollback Triggers**
- ❌ Migration failures
- ❌ Dependency installation failures
- ❌ Post-upgrade test failures
- ❌ Service restart failures

### **6. Monitoring & Logging**

#### **Log Files**
- **Main Log**: `logs/auto_upgrade.log`
- **System Log**: `journalctl -u zain-hms-autoupgrade.service`

#### **Log Monitoring**
```bash
# View auto-upgrade logs
tail -f logs/auto_upgrade.log

# View system service logs
journalctl -u zain-hms-autoupgrade.service -f

# Check last upgrade status
systemctl status zain-hms-autoupgrade.service
```

#### **Email Notifications** (Optional)
Create `scripts/notify_upgrade.py`:
```python
#!/usr/bin/env python3
import smtplib
from email.mime.text import MIMEText
import sys

def send_notification(status, details):
    # Email notification logic
    pass

if __name__ == '__main__':
    status = sys.argv[1]  # success/failure
    details = sys.argv[2] if len(sys.argv) > 2 else ""
    send_notification(status, details)
```

### **7. Backup Management**

#### **Backup Retention Policy**
```bash
# Add to crontab for cleanup
0 3 * * 0 find /var/www/zain_hms/backups/auto_upgrade -type d -mtime +30 -exec rm -rf {} \;
```

#### **Backup Verification**
```bash
# List available backups
ls -la backups/auto_upgrade/

# Restore from specific backup
python scripts/auto_upgrade.py --rollback backups/auto_upgrade/backup_20241123_020000
```

### **8. Emergency Procedures**

#### **Disable Auto-Upgrades**
```bash
# Temporarily stop
sudo systemctl stop zain-hms-autoupgrade.timer

# Permanently disable
sudo systemctl disable zain-hms-autoupgrade.timer
```

#### **Manual Rollback**
```bash
# If auto-rollback fails, manual rollback:
git reset --hard <previous_commit_hash>
cp backups/auto_upgrade/backup_YYYYMMDD_HHMMSS/db.sqlite3 .
sudo systemctl restart zain-hms nginx
```

#### **Emergency Contacts**
- System Administrator: [contact]
- On-call Engineer: [contact]
- Hosting Provider: [contact]

### **9. Testing & Validation**

#### **Test Environment Setup**
```bash
# Create test environment
git checkout -b test-autoupgrade
python scripts/auto_upgrade.py --force

# Validate in staging before production
```

#### **Dry-Run Mode** (Future Enhancement)
```bash
# Preview what would be updated
python scripts/auto_upgrade.py --dry-run
```

### **10. Security Considerations**

#### **File Permissions**
```bash
# Secure auto-upgrade script
chown root:www-data scripts/auto_upgrade.py
chmod 750 scripts/auto_upgrade.py

# Secure backup directory
chown -R www-data:www-data backups/
chmod 750 backups/auto_upgrade/
```

#### **Sudo Configuration**
Add to `/etc/sudoers.d/zain-hms`:
```bash
www-data ALL=(root) NOPASSWD: /bin/systemctl restart zain-hms
www-data ALL=(root) NOPASSWD: /bin/systemctl restart nginx
www-data ALL=(root) NOPASSWD: /bin/systemctl restart redis-server
```

---

## 🚀 **Quick Start Guide**

1. **Install Dependencies**: `pip install GitPython schedule`
2. **Copy Service Files**: Create systemd service and timer files
3. **Enable Timer**: `sudo systemctl enable zain-hms-autoupgrade.timer`
4. **Start Timer**: `sudo systemctl start zain-hms-autoupgrade.timer`
5. **Monitor**: `tail -f logs/auto_upgrade.log`

Your ZAIN HMS will now automatically check for and apply updates daily at 2 AM with full rollback capability for maximum safety! 🛡️