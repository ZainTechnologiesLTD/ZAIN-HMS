# ZAIN HMS Security Audit Management Command
# Comprehensive security assessment and reporting tool

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.cache import cache
from django.db import connection
from datetime import datetime, timedelta
import os
import json
import subprocess
import hashlib
from pathlib import Path

User = get_user_model()


class Command(BaseCommand):
    help = 'Perform comprehensive security audit of ZAIN HMS system'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--report-format',
            type=str,
            default='console',
            choices=['console', 'json', 'html'],
            help='Output format for security report'
        )
        parser.add_argument(
            '--save-report',
            type=str,
            help='Save report to specified file path'
        )
        parser.add_argument(
            '--fix-issues',
            action='store_true',
            help='Automatically fix security issues where possible'
        )
        
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.HTTP_INFO('🔍 Starting ZAIN HMS Security Audit...\n')
        )
        
        # Initialize audit results
        self.audit_results = {
            'timestamp': datetime.now().isoformat(),
            'system_info': self.get_system_info(),
            'security_checks': {},
            'recommendations': [],
            'critical_issues': [],
            'warnings': [],
            'passed_checks': []
        }
        
        # Run security checks
        self.check_django_security()
        self.check_database_security()
        self.check_authentication_security()
        self.check_file_permissions()
        self.check_sensitive_data_exposure()
        self.check_ssl_configuration()
        self.check_password_policies()
        self.check_session_security()
        self.check_logging_security()
        self.check_backup_security()
        
        # Generate report
        if options['report_format'] == 'json':
            self.generate_json_report()
        elif options['report_format'] == 'html':
            self.generate_html_report()
        else:
            self.generate_console_report()
            
        # Save report if requested
        if options['save_report']:
            self.save_report(options['save_report'], options['report_format'])
            
        # Auto-fix issues if requested
        if options['fix_issues']:
            self.auto_fix_issues()
            
        self.stdout.write(
            self.style.SUCCESS('✅ Security audit completed successfully!')
        )
        
    def get_system_info(self):
        """Gather basic system information"""
        return {
            'django_version': getattr(settings, 'DJANGO_VERSION', 'Unknown'),
            'python_version': subprocess.getoutput('python --version'),
            'debug_mode': getattr(settings, 'DEBUG', True),
            'allowed_hosts': getattr(settings, 'ALLOWED_HOSTS', []),
            'database_engine': settings.DATABASES['default']['ENGINE'],
            'cache_backend': getattr(settings, 'CACHES', {}).get('default', {}).get('BACKEND', 'Unknown'),
            'middleware': getattr(settings, 'MIDDLEWARE', []),
            'installed_apps_count': len(getattr(settings, 'INSTALLED_APPS', [])),
        }
        
    def check_django_security(self):
        """Check Django-specific security configurations"""
        checks = {}
        
        # DEBUG setting
        debug_enabled = getattr(settings, 'DEBUG', True)
        checks['debug_disabled'] = {
            'status': 'PASS' if not debug_enabled else 'FAIL',
            'message': 'DEBUG is disabled' if not debug_enabled else 'DEBUG is enabled in production!',
            'severity': 'CRITICAL' if debug_enabled else 'INFO'
        }
        
        # SECRET_KEY
        secret_key = getattr(settings, 'SECRET_KEY', '')
        checks['secret_key_secure'] = {
            'status': 'PASS' if len(secret_key) > 50 and 'django-insecure' not in secret_key else 'FAIL',
            'message': 'SECRET_KEY is properly configured' if len(secret_key) > 50 else 'SECRET_KEY is weak or default',
            'severity': 'CRITICAL' if len(secret_key) <= 50 else 'INFO'
        }
        
        # ALLOWED_HOSTS
        allowed_hosts = getattr(settings, 'ALLOWED_HOSTS', [])
        checks['allowed_hosts_configured'] = {
            'status': 'PASS' if allowed_hosts and '*' not in allowed_hosts else 'WARN',
            'message': 'ALLOWED_HOSTS properly configured' if allowed_hosts else 'ALLOWED_HOSTS not configured',
            'severity': 'HIGH' if not allowed_hosts or '*' in allowed_hosts else 'INFO'
        }
        
        # HTTPS settings
        ssl_redirect = getattr(settings, 'SECURE_SSL_REDIRECT', False)
        checks['https_enforced'] = {
            'status': 'PASS' if ssl_redirect else 'FAIL',
            'message': 'HTTPS redirect enabled' if ssl_redirect else 'HTTPS redirect disabled',
            'severity': 'HIGH' if not ssl_redirect else 'INFO'
        }
        
        # Security headers
        security_headers = [
            'SECURE_CONTENT_TYPE_NOSNIFF',
            'SECURE_BROWSER_XSS_FILTER',
            'SECURE_HSTS_SECONDS'
        ]
        
        for header in security_headers:
            enabled = getattr(settings, header, False)
            checks[f'{header.lower()}'] = {
                'status': 'PASS' if enabled else 'WARN',
                'message': f'{header} is {"enabled" if enabled else "disabled"}',
                'severity': 'MEDIUM' if not enabled else 'INFO'
            }
            
        self.audit_results['security_checks']['django_security'] = checks
        
    def check_database_security(self):
        """Check database security configurations"""
        checks = {}
        
        db_config = settings.DATABASES['default']
        
        # Database password
        has_password = bool(db_config.get('PASSWORD'))
        checks['database_password'] = {
            'status': 'PASS' if has_password else 'FAIL',
            'message': 'Database password configured' if has_password else 'Database has no password!',
            'severity': 'CRITICAL' if not has_password else 'INFO'
        }
        
        # SSL connection
        db_options = db_config.get('OPTIONS', {})
        ssl_enabled = 'sslmode' in db_options
        checks['database_ssl'] = {
            'status': 'PASS' if ssl_enabled else 'WARN',
            'message': 'Database SSL enabled' if ssl_enabled else 'Database SSL not configured',
            'severity': 'HIGH' if not ssl_enabled else 'INFO'
        }
        
        # Connection pooling and limits
        conn_max_age = db_config.get('CONN_MAX_AGE', 0)
        checks['connection_pooling'] = {
            'status': 'PASS' if conn_max_age > 0 else 'INFO',
            'message': f'Connection pooling configured ({conn_max_age}s)' if conn_max_age > 0 else 'Connection pooling not configured',
            'severity': 'LOW'
        }
        
        self.audit_results['security_checks']['database_security'] = checks
        
    def check_authentication_security(self):
        """Check authentication and authorization security"""
        checks = {}
        
        # Password validators
        password_validators = getattr(settings, 'AUTH_PASSWORD_VALIDATORS', [])
        checks['password_validators'] = {
            'status': 'PASS' if len(password_validators) >= 4 else 'WARN',
            'message': f'{len(password_validators)} password validators configured',
            'severity': 'MEDIUM' if len(password_validators) < 4 else 'INFO'
        }
        
        # Session configuration
        session_cookie_secure = getattr(settings, 'SESSION_COOKIE_SECURE', False)
        checks['secure_session_cookies'] = {
            'status': 'PASS' if session_cookie_secure else 'FAIL',
            'message': 'Session cookies secured' if session_cookie_secure else 'Session cookies not secured',
            'severity': 'HIGH' if not session_cookie_secure else 'INFO'
        }
        
        session_cookie_httponly = getattr(settings, 'SESSION_COOKIE_HTTPONLY', False)
        checks['httponly_session_cookies'] = {
            'status': 'PASS' if session_cookie_httponly else 'FAIL',
            'message': 'Session cookies HTTPOnly' if session_cookie_httponly else 'Session cookies not HTTPOnly',
            'severity': 'HIGH' if not session_cookie_httponly else 'INFO'
        }
        
        # CSRF protection
        csrf_cookie_secure = getattr(settings, 'CSRF_COOKIE_SECURE', False)
        checks['secure_csrf_cookies'] = {
            'status': 'PASS' if csrf_cookie_secure else 'FAIL',
            'message': 'CSRF cookies secured' if csrf_cookie_secure else 'CSRF cookies not secured',
            'severity': 'HIGH' if not csrf_cookie_secure else 'INFO'
        }
        
        # Check for default/weak admin users
        weak_users = User.objects.filter(
            is_superuser=True,
            username__in=['admin', 'administrator', 'root', 'test']
        ).count()
        checks['no_default_admin_users'] = {
            'status': 'PASS' if weak_users == 0 else 'WARN',
            'message': 'No default admin users found' if weak_users == 0 else f'{weak_users} default admin users found',
            'severity': 'MEDIUM' if weak_users > 0 else 'INFO'
        }
        
        self.audit_results['security_checks']['authentication_security'] = checks
        
    def check_file_permissions(self):
        """Check file and directory permissions"""
        checks = {}
        
        # Check settings file permissions
        try:
            settings_module_name = settings.SETTINGS_MODULE
            settings_module = __import__(settings_module_name, fromlist=[''])
            settings_file = Path(settings_module.__file__)
            if settings_file.exists():
                perms = oct(settings_file.stat().st_mode)[-3:]
                checks['settings_file_permissions'] = {
                    'status': 'PASS' if perms in ['644', '600'] else 'WARN',
                    'message': f'Settings file permissions: {perms}',
                    'severity': 'MEDIUM' if perms not in ['644', '600'] else 'INFO'
                }
        except:
            checks['settings_file_permissions'] = {
                'status': 'INFO',
                'message': 'Could not check settings file permissions',
                'severity': 'LOW'
            }
            
        # Check media directory permissions
        media_root = getattr(settings, 'MEDIA_ROOT', None)
        if media_root and Path(media_root).exists():
            perms = oct(Path(media_root).stat().st_mode)[-3:]
            checks['media_directory_permissions'] = {
                'status': 'PASS' if perms in ['755', '750'] else 'WARN',
                'message': f'Media directory permissions: {perms}',
                'severity': 'MEDIUM' if perms not in ['755', '750'] else 'INFO'
            }
            
        # Check for .env file exposure
        env_files = ['.env', '.env.local', '.env.production']
        exposed_env = []
        for env_file in env_files:
            env_path = Path(env_file)
            if env_path.exists():
                static_url = getattr(settings, 'STATIC_URL', '/static/')
                media_url = getattr(settings, 'MEDIA_URL', '/media/')
                # Check if env file is in public directories
                if static_url in str(env_path) or media_url in str(env_path):
                    exposed_env.append(env_file)
                    
        checks['env_files_secure'] = {
            'status': 'PASS' if not exposed_env else 'CRITICAL',
            'message': 'Environment files secure' if not exposed_env else f'Exposed env files: {exposed_env}',
            'severity': 'CRITICAL' if exposed_env else 'INFO'
        }
        
        self.audit_results['security_checks']['file_permissions'] = checks
        
    def check_sensitive_data_exposure(self):
        """Check for sensitive data exposure"""
        checks = {}
        
        # Check for hardcoded secrets in settings
        try:
            settings_module_name = settings.SETTINGS_MODULE
            settings_module = __import__(settings_module_name, fromlist=[''])
            settings_file = settings_module.__file__
            if settings_file and Path(settings_file).exists():
                with open(settings_file, 'r') as f:
                    content = f.read().lower()
                    
                suspicious_patterns = [
                    'password = ', 'secret_key = ', 'api_key = ',
                    'token = ', 'aws_secret', 'database_url = '
                ]
                
                found_hardcoded = any(pattern in content for pattern in suspicious_patterns)
                checks['no_hardcoded_secrets'] = {
                    'status': 'PASS' if not found_hardcoded else 'WARN',
                    'message': 'No hardcoded secrets found' if not found_hardcoded else 'Potential hardcoded secrets found',
                    'severity': 'HIGH' if found_hardcoded else 'INFO'
                }
        except:
            checks['no_hardcoded_secrets'] = {
                'status': 'INFO',
                'message': 'Could not check for hardcoded secrets',
                'severity': 'LOW'
            }
            
        # Check for exposed admin URLs
        admin_url = getattr(settings, 'ADMIN_URL', 'admin/')
        checks['admin_url_changed'] = {
            'status': 'PASS' if admin_url != 'admin/' else 'WARN',
            'message': 'Admin URL changed from default' if admin_url != 'admin/' else 'Using default admin URL',
            'severity': 'MEDIUM' if admin_url == 'admin/' else 'INFO'
        }
        
        self.audit_results['security_checks']['sensitive_data_exposure'] = checks
        
    def check_ssl_configuration(self):
        """Check SSL/TLS configuration"""
        checks = {}
        
        # HSTS configuration
        hsts_seconds = getattr(settings, 'SECURE_HSTS_SECONDS', 0)
        checks['hsts_enabled'] = {
            'status': 'PASS' if hsts_seconds > 0 else 'WARN',
            'message': f'HSTS configured for {hsts_seconds} seconds' if hsts_seconds > 0 else 'HSTS not configured',
            'severity': 'MEDIUM' if hsts_seconds == 0 else 'INFO'
        }
        
        hsts_include_subdomains = getattr(settings, 'SECURE_HSTS_INCLUDE_SUBDOMAINS', False)
        checks['hsts_subdomains'] = {
            'status': 'PASS' if hsts_include_subdomains else 'INFO',
            'message': 'HSTS includes subdomains' if hsts_include_subdomains else 'HSTS does not include subdomains',
            'severity': 'LOW'
        }
        
        # SSL proxy configuration
        ssl_proxy_header = getattr(settings, 'SECURE_PROXY_SSL_HEADER', None)
        checks['ssl_proxy_configured'] = {
            'status': 'PASS' if ssl_proxy_header else 'INFO',
            'message': 'SSL proxy header configured' if ssl_proxy_header else 'SSL proxy header not configured',
            'severity': 'LOW'
        }
        
        self.audit_results['security_checks']['ssl_configuration'] = checks
        
    def check_password_policies(self):
        """Check password policy enforcement"""
        checks = {}
        
        # Custom password validators
        has_healthcare_validator = any(
            'HealthcarePasswordValidator' in str(validator)
            for validator in getattr(settings, 'AUTH_PASSWORD_VALIDATORS', [])
        )
        checks['healthcare_password_validator'] = {
            'status': 'PASS' if has_healthcare_validator else 'WARN',
            'message': 'Healthcare password validator enabled' if has_healthcare_validator else 'Healthcare password validator not configured',
            'severity': 'MEDIUM' if not has_healthcare_validator else 'INFO'
        }
        
        # Password expiry settings
        hipaa_compliance = getattr(settings, 'HIPAA_COMPLIANCE', {})
        password_expiry = hipaa_compliance.get('PASSWORD_EXPIRY_DAYS', 0)
        checks['password_expiry_configured'] = {
            'status': 'PASS' if password_expiry > 0 else 'WARN',
            'message': f'Password expiry set to {password_expiry} days' if password_expiry > 0 else 'Password expiry not configured',
            'severity': 'MEDIUM' if password_expiry == 0 else 'INFO'
        }
        
        self.audit_results['security_checks']['password_policies'] = checks
        
    def check_session_security(self):
        """Check session security configuration"""
        checks = {}
        
        # Session timeout
        session_timeout = getattr(settings, 'SESSION_TIMEOUT', 0)
        checks['session_timeout_configured'] = {
            'status': 'PASS' if session_timeout > 0 else 'WARN',
            'message': f'Session timeout set to {session_timeout} seconds' if session_timeout > 0 else 'Session timeout not configured',
            'severity': 'MEDIUM' if session_timeout == 0 else 'INFO'
        }
        
        # Session cookie age
        session_cookie_age = getattr(settings, 'SESSION_COOKIE_AGE', 1209600)  # Default 2 weeks
        checks['session_cookie_age'] = {
            'status': 'PASS' if session_cookie_age <= 3600 else 'WARN',
            'message': f'Session cookie age: {session_cookie_age} seconds',
            'severity': 'MEDIUM' if session_cookie_age > 3600 else 'INFO'
        }
        
        # Session expire at browser close
        expire_at_close = getattr(settings, 'SESSION_EXPIRE_AT_BROWSER_CLOSE', False)
        checks['session_expire_at_close'] = {
            'status': 'PASS' if expire_at_close else 'WARN',
            'message': 'Sessions expire at browser close' if expire_at_close else 'Sessions persist after browser close',
            'severity': 'MEDIUM' if not expire_at_close else 'INFO'
        }
        
        self.audit_results['security_checks']['session_security'] = checks
        
    def check_logging_security(self):
        """Check security logging configuration"""
        checks = {}
        
        # Logging configuration
        logging_config = getattr(settings, 'LOGGING', {})
        has_security_logger = 'django.security' in logging_config.get('loggers', {})
        checks['security_logging_enabled'] = {
            'status': 'PASS' if has_security_logger else 'WARN',
            'message': 'Security logging enabled' if has_security_logger else 'Security logging not configured',
            'severity': 'MEDIUM' if not has_security_logger else 'INFO'
        }
        
        # Audit logging
        has_audit_logger = 'zain_hms.audit' in logging_config.get('loggers', {})
        checks['audit_logging_enabled'] = {
            'status': 'PASS' if has_audit_logger else 'WARN',
            'message': 'Audit logging enabled' if has_audit_logger else 'Audit logging not configured',
            'severity': 'HIGH' if not has_audit_logger else 'INFO'
        }
        
        self.audit_results['security_checks']['logging_security'] = checks
        
    def check_backup_security(self):
        """Check backup security configuration"""
        checks = {}
        
        # Backup encryption
        backup_encrypt = getattr(settings, 'DBBACKUP_ENCRYPT', False)
        checks['backup_encryption_enabled'] = {
            'status': 'PASS' if backup_encrypt else 'WARN',
            'message': 'Backup encryption enabled' if backup_encrypt else 'Backup encryption not enabled',
            'severity': 'HIGH' if not backup_encrypt else 'INFO'
        }
        
        # Backup location security
        backup_location = str(getattr(settings, 'DBBACKUP_STORAGE_OPTIONS', {}).get('location', ''))
        secure_backup_location = '/var/backups' in backup_location or 's3://' in backup_location
        checks['secure_backup_location'] = {
            'status': 'PASS' if secure_backup_location else 'WARN',
            'message': 'Secure backup location configured' if secure_backup_location else 'Backup location may be insecure',
            'severity': 'MEDIUM' if not secure_backup_location else 'INFO'
        }
        
        self.audit_results['security_checks']['backup_security'] = checks
        
    def generate_console_report(self):
        """Generate console output report"""
        self.stdout.write('\n' + '='*80)
        self.stdout.write(self.style.HTTP_INFO('ZAIN HMS SECURITY AUDIT REPORT'))
        self.stdout.write('='*80 + '\n')
        
        # Summary statistics
        total_checks = sum(len(checks) for checks in self.audit_results['security_checks'].values())
        critical_count = len([c for c in self.get_all_checks() if c['severity'] == 'CRITICAL'])
        high_count = len([c for c in self.get_all_checks() if c['severity'] == 'HIGH'])
        passed_count = len([c for c in self.get_all_checks() if c['status'] == 'PASS'])
        
        self.stdout.write(f"📊 SUMMARY:")
        self.stdout.write(f"   Total Checks: {total_checks}")
        self.stdout.write(f"   ✅ Passed: {passed_count}")
        self.stdout.write(f"   🔴 Critical: {critical_count}")
        self.stdout.write(f"   🟠 High: {high_count}")
        self.stdout.write()
        
        # Display each category
        for category, checks in self.audit_results['security_checks'].items():
            self.stdout.write(f"\n🔍 {category.upper().replace('_', ' ')}:")
            for check_name, check_info in checks.items():
                status_icon = '✅' if check_info['status'] == 'PASS' else '❌' if check_info['status'] == 'FAIL' else '⚠️'
                self.stdout.write(f"   {status_icon} {check_info['message']}")
                
        # Critical issues
        if critical_count > 0:
            self.stdout.write('\n' + '='*80)
            self.stdout.write(self.style.ERROR('🚨 CRITICAL SECURITY ISSUES FOUND:'))
            self.stdout.write('='*80)
            for check in self.get_all_checks():
                if check['severity'] == 'CRITICAL':
                    self.stdout.write(f"❌ {check['message']}")
                    
        self.stdout.write('\n' + '='*80)
        
    def generate_json_report(self):
        """Generate JSON format report"""
        self.stdout.write(json.dumps(self.audit_results, indent=2))
        
    def generate_html_report(self):
        """Generate HTML format report"""
        # This could be expanded to create a full HTML report
        self.stdout.write("<h1>ZAIN HMS Security Audit Report</h1>")
        self.stdout.write(f"<p>Generated: {self.audit_results['timestamp']}</p>")
        # Add more HTML generation as needed
        
    def get_all_checks(self):
        """Get all checks from all categories"""
        all_checks = []
        for category, checks in self.audit_results['security_checks'].items():
            all_checks.extend(checks.values())
        return all_checks
        
    def save_report(self, file_path, format_type):
        """Save report to file"""
        with open(file_path, 'w') as f:
            if format_type == 'json':
                json.dump(self.audit_results, f, indent=2)
            else:
                f.write("ZAIN HMS Security Audit Report\n")
                f.write("=" * 40 + "\n")
                # Add more content as needed
                
        self.stdout.write(
            self.style.SUCCESS(f"Report saved to: {file_path}")
        )
        
    def auto_fix_issues(self):
        """Automatically fix security issues where possible"""
        self.stdout.write(
            self.style.WARNING('\n🔧 Auto-fixing security issues...')
        )
        
        # This could include automatic fixes for common issues
        # For now, just provide recommendations
        self.stdout.write(
            self.style.WARNING('Auto-fix not yet implemented. Please review critical issues manually.')
        )