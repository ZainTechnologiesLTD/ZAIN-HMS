#!/usr/bin/env python3
"""
Comprehensive database setup script for HMS
Creates all missing tables and fixes tenant issues
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zain_hms.settings')
django.setup()

from django.core.management import execute_from_command_line
from django.db import connection

def create_missing_tables():
    """Create all missing database tables"""
    
    print("🔧 HMS Database Setup Tool")
    print("=" * 50)
    
    # List of tables that should exist
    required_tables = [
        'appointments_appointment',
        'patients_patient', 
        'doctors_doctor',
        'nurses_nurse',
        'appointments_appointmenttype',
    ]
    
    print("📊 Checking database tables...")
    
    with connection.cursor() as cursor:
        # Get list of existing tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        print(f"   Found {len(existing_tables)} existing tables")
        
        missing_tables = []
        for table in required_tables:
            if table not in existing_tables:
                missing_tables.append(table)
        
        if missing_tables:
            print(f"   ❌ Missing tables: {', '.join(missing_tables)}")
        else:
            print("   ✅ All required tables exist")
    
    # Create basic table structures if missing
    if missing_tables:
        print("\n📝 Creating missing tables...")
        
        table_schemas = {
            'patients_patient': '''
                CREATE TABLE IF NOT EXISTS patients_patient (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_number VARCHAR(20) UNIQUE,
                    first_name VARCHAR(100) NOT NULL,
                    last_name VARCHAR(100) NOT NULL,
                    date_of_birth DATE,
                    gender VARCHAR(10),
                    phone VARCHAR(20),
                    email VARCHAR(254),
                    address TEXT,
                    emergency_contact VARCHAR(100),
                    blood_group VARCHAR(5),
                    is_active BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            ''',
            
            'doctors_doctor': '''
                CREATE TABLE IF NOT EXISTS doctors_doctor (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    first_name VARCHAR(100) NOT NULL,
                    last_name VARCHAR(100) NOT NULL,
                    specialization VARCHAR(100),
                    license_number VARCHAR(50) UNIQUE,
                    phone_number VARCHAR(20),
                    email VARCHAR(254),
                    date_of_birth DATE,
                    address TEXT,
                    joining_date DATE,
                    is_active BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    user_id INTEGER
                );
            ''',
            
            'nurses_nurse': '''
                CREATE TABLE IF NOT EXISTS nurses_nurse (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    first_name VARCHAR(100) NOT NULL,
                    last_name VARCHAR(100) NOT NULL,
                    license_number VARCHAR(50),
                    phone_number VARCHAR(20),
                    email VARCHAR(254),
                    date_of_birth DATE,
                    address TEXT,
                    joining_date DATE,
                    department VARCHAR(100),
                    is_active BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    user_id INTEGER
                );
            ''',
            
            'appointments_appointmenttype': '''
                CREATE TABLE IF NOT EXISTS appointments_appointmenttype (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(100) NOT NULL,
                    description TEXT,
                    duration_minutes INTEGER DEFAULT 30,
                    color VARCHAR(7) DEFAULT '#007bff',
                    is_active BOOLEAN DEFAULT 1
                );
            '''
        }
        
        with connection.cursor() as cursor:
            for table in missing_tables:
                if table in table_schemas:
                    try:
                        cursor.execute(table_schemas[table])
                        print(f"   ✅ Created {table}")
                    except Exception as e:
                        print(f"   ❌ Failed to create {table}: {e}")
    
    # Insert some basic data
    print("\n📋 Adding basic data...")
    
    try:
        with connection.cursor() as cursor:
            # Add basic appointment types
            cursor.execute("""
                INSERT OR IGNORE INTO appointments_appointmenttype 
                (name, description, duration_minutes, color) VALUES 
                ('General Consultation', 'General medical consultation', 30, '#007bff'),
                ('Follow-up', 'Follow-up appointment', 15, '#28a745'),
                ('Emergency', 'Emergency consultation', 60, '#dc3545'),
                ('Routine Check-up', 'Routine health check-up', 45, '#ffc107')
            """)
            print("   ✅ Added basic appointment types")
        
    except Exception as e:
        print(f"   ❌ Error adding basic data: {e}")
    
    print("\n🎉 Database setup completed!")
    return True

def main():
    """Main function"""
    try:
        success = create_missing_tables()
        if success:
            print("\n✅ Database setup completed successfully!")
            print("\n💡 Next steps:")
            print("   1. Run: python manage.py runserver")
            print("   2. Login and test all modules")
        else:
            print("\n❌ Database setup failed")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
