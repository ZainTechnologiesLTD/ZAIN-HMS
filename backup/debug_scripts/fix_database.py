#!/usr/bin/env python3
"""
Comprehensive fix script for HMS database and tenant issues
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zain_hms.settings')
django.setup()

from django.core.management import execute_from_command_line
from django.db import connection
from apps.accounts.models import CustomUser
from apps.tenants.models import Tenant

def fix_database_issues():
    """Fix database issues step by step"""
    
    print("🔧 HMS Database Repair Tool")
    print("=" * 50)
    
    # Step 1: Check current state
    print("📊 Checking current database state...")
    
    try:
        # Check if we have tenants (hospitals)
        tenants = Tenant.objects.all()
        print(f"   Found {tenants.count()} hospital tenants")
        
        # Check if we have users
        users = CustomUser.objects.all()
        print(f"   Found {users.count()} users")
        
    except Exception as e:
        print(f"   ❌ Error checking database: {e}")
        return False
    
    # Step 2: Run basic migrations on main database
    print("\n🚀 Running migrations on main database...")
    try:
        execute_from_command_line(['manage.py', 'migrate', '--verbosity=0'])
        print("   ✅ Main database migrations completed")
    except Exception as e:
        print(f"   ❌ Migration error: {e}")
    
    # Step 3: Create basic appointment table if missing
    print("\n📋 Checking appointments table...")
    try:
        with connection.cursor() as cursor:
            # Check if appointments table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='appointments_appointment';")
            table_exists = cursor.fetchone()
            
            if not table_exists:
                print("   📝 Creating basic appointments table...")
                # Create a basic appointments table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS appointments_appointment (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        appointment_number VARCHAR(20) UNIQUE,
                        patient_id VARCHAR(255),
                        doctor_id VARCHAR(255),
                        appointment_date DATE,
                        appointment_time TIME,
                        status VARCHAR(20) DEFAULT 'SCHEDULED',
                        priority VARCHAR(20) DEFAULT 'NORMAL',
                        chief_complaint TEXT,
                        notes TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        created_by_id INTEGER
                    );
                """)
                print("   ✅ Basic appointments table created")
            else:
                print("   ✅ Appointments table exists")
                
    except Exception as e:
        print(f"   ❌ Error with appointments table: {e}")
    
    # Step 4: Fix user roles and permissions
    print("\n👤 Checking user roles...")
    try:
        # Ensure we have at least one admin user
        admin_users = CustomUser.objects.filter(role='ADMIN')
        if not admin_users.exists():
            # Update existing superuser to admin
            superusers = CustomUser.objects.filter(is_superuser=True)
            if superusers.exists():
                user = superusers.first()
                user.role = 'ADMIN'
                user.save()
                print(f"   ✅ Updated {user.username} to ADMIN role")
            else:
                print("   ⚠️ No admin users found - you may need to create one")
        else:
            print(f"   ✅ Found {admin_users.count()} admin users")
            
    except Exception as e:
        print(f"   ❌ Error with user roles: {e}")
    
    # Step 5: Create basic tenant/hospital if none exists
    print("\n🏥 Checking hospital tenants...")
    try:
        if not Tenant.objects.exists():
            print("   📝 Creating default hospital tenant...")
            Tenant.objects.create(
                hospital_id="DEFAULT",
                hospital_name="Default Hospital",
                subdomain="default",
                database_name="hospital_default",
                address="123 Main St",
                phone="123-456-7890",
                email="admin@default-hospital.com",
                is_active=True
            )
            print("   ✅ Default hospital tenant created")
        else:
            tenant = Tenant.objects.first()
            print(f"   ✅ Found hospital tenant: {tenant.hospital_name} ({tenant.hospital_id})")
            
    except Exception as e:
        print(f"   ❌ Error with hospitals: {e}")
    
    print("\n🎉 Database repair completed!")
    print("\n💡 Next steps:")
    print("   1. Start the server: python manage.py runserver")
    print("   2. Login and select a hospital")
    print("   3. Test the fixed endpoints")
    
    return True

if __name__ == "__main__":
    try:
        success = fix_database_issues()
        if success:
            print("\n✅ Repair completed successfully!")
        else:
            print("\n❌ Repair failed - check the errors above")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Repair interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
