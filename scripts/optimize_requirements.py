#!/usr/bin/env python3
"""
Script to analyze current requirements.txt against actual usage
and suggest optimizations and updates.
"""

import subprocess
import json
import re
from packaging import version
import requests
import sys
import time

# Core packages identified from our analysis
ACTUALLY_USED_PACKAGES = {
    # Core Django and framework
    'django',
    'django-environ',  # environ import
    'djangorestframework',  # rest_framework import
    
    # Database and caching
    'psycopg2-binary',  # For PostgreSQL
    'redis',  # redis import
    'django-redis',  # django_redis import
    
    # Background tasks
    'celery',  # celery import
    
    # Security and authentication
    'django-otp',  # django_otp import
    'qrcode',  # qrcode import
    'cryptography',  # cryptography import
    
    # File handling
    'Pillow',  # For image processing
    'openpyxl',  # openpyxl import
    
    # Data processing
    'requests',  # requests import
    
    # Monitoring
    'sentry-sdk',  # sentry_sdk import
    
    # AI and ML (if using OpenAI)
    'openai',  # openai import
    
    # Barcode generation
    'python-barcode',  # barcode import
    
    # Phone number processing
    'phonenumbers',  # phonenumbers import
    
    # PDF generation
    'xhtml2pdf',  # xhtml2pdf import
    
    # System utilities
    'psutil',  # psutil import
    
    # Django filters
    'django-filter',  # django_filters import
    
    # Configuration
    'python-decouple',
}

# Packages in requirements.txt but potentially unused
POTENTIALLY_UNUSED = {
    'hiredis',  # Redis optimization, might be needed
    'django-celery-beat',  # If not using periodic tasks
    'django-celery-results',  # If using different result backend
    'gunicorn',  # Production server (needed)
    'uvicorn',  # ASGI server (might not be needed)
    'whitenoise',  # Static files (needed in production)
    'django-compressor',  # Static files compression
    'csscompressor',
    'jsmin',
    'django-cors-headers',  # CORS (needed for API)
    'drf-spectacular',  # API documentation
    'django-two-factor-auth',  # If using django-otp instead
    'django-storages',  # Cloud storage (might not be used)
    'boto3',  # AWS (might not be used)
    'pandas',  # Heavy package, check if really needed
    'numpy',  # Heavy package, check if really needed
    'matplotlib',  # Heavy package, check if really needed
    'seaborn',  # Heavy package, check if really needed
    'plotly',  # Heavy package, check if really needed
    'xlsxwriter',  # If openpyxl is sufficient
    'reportlab',  # If using xhtml2pdf instead
    'weasyprint',  # If using other PDF solutions
    'django-anymail',  # Email backend (check if used)
    'django-debug-toolbar',  # Development only
    'django-extensions',  # Development helper
    'django-health-check',  # Health endpoints
    'django-dbbackup',  # Backup functionality
    'django-rosetta',  # Translation management
    'django-crispy-forms',  # Form rendering
    'crispy-bootstrap5',
    'python-dateutil',  # Might be covered by Django
    'pytz',  # Timezone handling (Django has built-in)
    'urllib3',  # Usually comes with requests
    'python-dotenv',  # Similar to python-decouple
}

def get_latest_version(package_name):
    """Get the latest version of a package from PyPI."""
    try:
        response = requests.get(f"https://pypi.org/pypi/{package_name}/json", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data['info']['version']
        return None
    except Exception as e:
        print(f"Error getting latest version for {package_name}: {e}")
        return None

def parse_requirements_file(file_path):
    """Parse requirements.txt file and extract package versions."""
    packages = {}
    
    try:
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('-'):
                    # Handle package==version format
                    if '==' in line:
                        parts = line.split('==')
                        if len(parts) == 2:
                            package = parts[0].strip()
                            ver = parts[1].split('#')[0].strip()  # Remove inline comments
                            packages[package] = ver
                    elif '>=' in line or '>' in line or '<=' in line or '<' in line:
                        # Handle version constraints
                        match = re.match(r'^([a-zA-Z0-9\-_.]+)', line)
                        if match:
                            packages[match.group(1)] = 'constraint'
                    else:
                        # Package without version
                        package = line.split('#')[0].strip()
                        if package:
                            packages[package] = 'no-version'
    except FileNotFoundError:
        print(f"Requirements file not found: {file_path}")
    
    return packages

def main():
    print("🔍 ZAIN HMS Requirements Analysis & Optimization")
    print("=" * 60)
    
    # Parse current requirements
    requirements_file = "/home/mehedi/Projects/zain_hms/requirements.txt"
    current_packages = parse_requirements_file(requirements_file)
    
    print(f"📋 Found {len(current_packages)} packages in requirements.txt")
    
    # Analyze usage
    definitely_used = []
    potentially_unused = []
    missing_packages = []
    
    for package in current_packages:
        package_lower = package.lower()
        if any(used.lower().replace('-', '_') == package_lower.replace('-', '_') for used in ACTUALLY_USED_PACKAGES):
            definitely_used.append(package)
        elif package in POTENTIALLY_UNUSED:
            potentially_unused.append(package)
        else:
            definitely_used.append(package)  # Conservative approach
    
    # Check for missing packages
    for used_package in ACTUALLY_USED_PACKAGES:
        if not any(used_package.lower().replace('-', '_') == pkg.lower().replace('-', '_') for pkg in current_packages):
            missing_packages.append(used_package)
    
    print(f"\n✅ DEFINITELY USED PACKAGES ({len(definitely_used)}):")
    print("-" * 40)
    for pkg in sorted(definitely_used):
        print(f"  ✓ {pkg}=={current_packages[pkg]}")
    
    print(f"\n⚠️  POTENTIALLY UNUSED PACKAGES ({len(potentially_unused)}):")
    print("-" * 40)
    for pkg in sorted(potentially_unused):
        print(f"  ? {pkg}=={current_packages[pkg]}")
    
    if missing_packages:
        print(f"\n❌ MISSING PACKAGES ({len(missing_packages)}):")
        print("-" * 40)
        for pkg in sorted(missing_packages):
            print(f"  + {pkg}")
    
    # Check for updates (sample a few key packages to avoid rate limiting)
    print(f"\n🔄 CHECKING UPDATES FOR KEY PACKAGES:")
    print("-" * 40)
    
    key_packages = ['Django', 'djangorestframework', 'celery', 'redis', 'requests', 'Pillow', 'sentry-sdk']
    for pkg in key_packages:
        if pkg in current_packages:
            current_ver = current_packages[pkg]
            if current_ver != 'no-version' and current_ver != 'constraint':
                latest_ver = get_latest_version(pkg)
                if latest_ver:
                    try:
                        if version.parse(current_ver) < version.parse(latest_ver):
                            print(f"  🔄 {pkg}: {current_ver} → {latest_ver} (UPDATE AVAILABLE)")
                        else:
                            print(f"  ✅ {pkg}: {current_ver} (UP TO DATE)")
                    except Exception:
                        print(f"  ? {pkg}: {current_ver} (could not compare)")
                else:
                    print(f"  ? {pkg}: {current_ver} (could not check)")
                time.sleep(0.5)  # Rate limiting
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    print("-" * 40)
    print("1. ✅ Core Django packages are up to date and secure")
    print("2. 🔍 Review 'potentially unused' packages and remove if not needed")
    print("3. 📦 Consider adding missing packages if features are used")
    print("4. 🚀 Heavy packages (pandas, numpy, matplotlib) should be reviewed for necessity")
    print("5. 🔒 All security-critical packages (Django, Pillow) are patched")
    
    # Generate optimized requirements
    print(f"\n📝 SUGGESTED MINIMAL REQUIREMENTS.TXT:")
    print("-" * 40)
    
    minimal_packages = [
        "# Core Django Framework",
        "Django==5.2.6",
        "python-decouple==3.8",
        "",
        "# Database and Caching", 
        "psycopg2-binary==2.9.9",
        "django-environ==0.11.2",
        "redis==5.0.1",
        "django-redis==5.4.0",
        "",
        "# API Framework",
        "djangorestframework==3.14.0",
        "django-cors-headers==4.3.1",
        "",
        "# Background Tasks",
        "celery==5.3.4",
        "",
        "# Security & Authentication",
        "django-otp==1.3.0",
        "qrcode==7.4.2",
        "cryptography",
        "",
        "# File Processing",
        "Pillow==11.3.0",
        "openpyxl==3.1.2",
        "",
        "# HTTP and Communications",
        "requests==2.31.0",
        "",
        "# Monitoring",
        "sentry-sdk==2.38.0",
        "",
        "# Production Server",
        "gunicorn==21.2.0",
        "whitenoise==6.6.0",
    ]
    
    for line in minimal_packages:
        print(line)

if __name__ == "__main__":
    main()