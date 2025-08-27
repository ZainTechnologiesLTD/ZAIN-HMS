# Database Initialization for Multi-Tenant Hospital Management System

"""
This module handles the dynamic creation and management of hospital-specific databases
for the multi-tenant SaaS system. Each hospital gets its own database for complete
data isolation.
"""

import os
import sqlite3
from pathlib import Path
from django.conf import settings
from django.core.management import call_command
from django.db import connections
from apps.core.db_router import TenantDatabaseManager


def initialize_hospital_database(hospital_code, create_directories=True):
    """
    Initialize a hospital database with proper tables and schema
    """
    print(f"Initializing database for hospital: {hospital_code}")
    
    # Create hospital directory
    hospital_dir = settings.BASE_DIR / f'hospitals/{hospital_code}'
    if create_directories:
        hospital_dir.mkdir(parents=True, exist_ok=True)
    
    # Database file path
    db_path = hospital_dir / 'db.sqlite3'
    
    # Create the SQLite database file directly
    if not db_path.exists():
        print(f"Creating database file: {db_path}")
        conn = sqlite3.connect(str(db_path))
        conn.close()
    
    # Add database configuration to Django settings
    db_name = f"hospital_{hospital_code}"
    db_config = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': str(db_path),
        'OPTIONS': {
            'timeout': 20,
        },
        'ATOMIC_REQUESTS': False,
        'AUTOCOMMIT': True,
        'CONN_MAX_AGE': 0,
        'CONN_HEALTH_CHECKS': False,
        'TIME_ZONE': None,
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
        'TEST': {
            'CHARSET': None,
            'COLLATION': None,
            'MIGRATE': True,
            'MIRROR': None,
            'NAME': None
        }
    }
    
    # Add to settings
    settings.DATABASES[db_name] = db_config
    
    # Force connections refresh
    connections.close_all()
    if hasattr(connections, '_connections'):
        import threading
        connections._connections = threading.local()
    
    # Run migrations directly using Django's low-level migration system
    print(f"Running migrations for {db_name}...")
    
    # Set hospital context
    TenantDatabaseManager.set_hospital_context(hospital_code)
    
    try:
        # First migrate core Django apps that are required
        core_apps = ['contenttypes', 'auth']
        for app in core_apps:
            try:
                print(f"  Migrating core {app}...")
                call_command('migrate', app, database=db_name, verbosity=0, interactive=False)
                print(f"  ✓ {app}")
            except Exception as e:
                print(f"  ✗ {app}: {e}")
        
        # List of tenant apps that need migration
        tenant_apps = [
            'patients', 'appointments', 'doctors', 'nurses', 'staff',
            'billing', 'pharmacy', 'laboratory', 'radiology', 'emergency',
            'inventory', 'reports', 'analytics', 'hr', 'surgery',
            'telemedicine', 'room_management', 'opd', 'ipd',
            'notifications', 'contact', 'feedback', 'dashboard'
        ]
        
        # Apply migrations for each app
        for app in tenant_apps:
            try:
                print(f"  Migrating {app}...")
                call_command('migrate', app, database=db_name, verbosity=0, interactive=False)
                print(f"  ✓ {app}")
            except Exception as e:
                print(f"  ✗ {app}: {e}")
                
        print(f"✓ Database initialization completed for {hospital_code}")
        return True
        
    except Exception as e:
        print(f"✗ Failed to initialize database for {hospital_code}: {e}")
        return False
    finally:
        # Clear hospital context
        TenantDatabaseManager.set_hospital_context(None)


def initialize_all_hospital_databases():
    """
    Initialize databases for all existing hospitals
    """
    from apps.accounts.models import Hospital
    
    print("Initializing databases for all hospitals...")
    hospitals = Hospital.objects.all()
    
    success_count = 0
    for hospital in hospitals:
        if initialize_hospital_database(hospital.code):
            success_count += 1
    
    print(f"Successfully initialized {success_count}/{len(hospitals)} hospital databases")
    return success_count == len(hospitals)


def verify_hospital_database(hospital_code):
    """
    Verify that a hospital database exists and has the correct tables
    """
    hospital_dir = settings.BASE_DIR / f'hospitals/{hospital_code}'
    db_path = hospital_dir / 'db.sqlite3'
    
    if not db_path.exists():
        return False, "Database file does not exist"
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check for some key tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        
        # Check if we have expected tables
        expected_tables = ['patients_patient', 'appointments_appointment', 'doctors_doctor']
        missing_tables = [table for table in expected_tables if table not in tables]
        
        if missing_tables:
            return False, f"Missing tables: {missing_tables}"
        
        return True, f"Database verified with {len(tables)} tables"
        
    except Exception as e:
        return False, f"Database verification failed: {e}"


if __name__ == "__main__":
    # This can be run as a standalone script
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zain_hms.settings')
    django.setup()
    
    initialize_all_hospital_databases()
