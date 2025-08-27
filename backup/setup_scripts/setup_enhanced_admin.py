#!/usr/bin/env python3
"""
Setup script for Zain HMS Enhanced Admin UI
This script applies all the enhancements to your admin interface
"""

import os
import sys
import django
from pathlib import Path

# Setup Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zain_hms.settings')
django.setup()

from django.core.management import call_command
from django.contrib.auth import get_user_model
User = get_user_model()
from django.conf import settings


def main():
    print("🏥 Zain HMS Enhanced Admin UI Setup")
    print("=" * 50)
    
    # Collect static files
    print("\n📦 Collecting static files...")
    try:
        call_command('collectstatic', '--noinput')
        print("✅ Static files collected successfully")
    except Exception as e:
        print(f"⚠️  Static files collection warning: {e}")
    
    # Run migrations
    print("\n🔄 Running database migrations...")
    try:
        call_command('migrate', '--run-syncdb')
        print("✅ Database migrations completed")
    except Exception as e:
        print(f"❌ Migration error: {e}")
    
    # Setup enhanced admin
    print("\n🎨 Setting up enhanced admin...")
    try:
        call_command('setup_enhanced_admin', '--apply-permissions')
        print("✅ Enhanced admin setup completed")
    except Exception as e:
        print(f"⚠️  Admin setup note: {e}")
    
    # Check if superuser exists
    print("\n👤 Checking superuser...")
    if not User.objects.filter(is_superuser=True).exists():
        print("No superuser found. Creating one...")
        call_command('createsuperuser')
    else:
        print("✅ Superuser already exists")
    
    print("\n" + "=" * 50)
    print("🎉 ENHANCED ADMIN UI SETUP COMPLETE!")
    print("=" * 50)
    print("\n🔗 Access your enhanced admin interface at:")
    print("   http://localhost:8000/admin/")
    print("\n✨ Features enabled:")
    print("   • Modern Jazzmin theme with custom styling")
    print("   • Enhanced dashboard with real-time analytics")
    print("   • Advanced filtering and search capabilities")
    print("   • CSV/JSON export functionality")
    print("   • Dark/Light theme toggle")
    print("   • Responsive design for mobile devices")
    print("   • Custom admin actions and bulk operations")
    print("   • Professional color scheme and typography")
    print("\n🚀 Start your server with:")
    print("   python manage.py runserver")
    print("\n📚 Additional resources:")
    print("   • Dashboard: /admin/dashboard/")
    print("   • Analytics: /admin/analytics/")
    print("   • API Stats: /admin/api/stats/")


if __name__ == '__main__':
    main()
