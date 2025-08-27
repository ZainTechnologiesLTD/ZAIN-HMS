#!/usr/bin/env python3
"""
Script to add the role field to the CustomUser model
"""
import os
import django
import sqlite3

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zain_hms.settings')
django.setup()

from django.db import connection

def add_role_field():
    """Add the role field and other new fields to the accounts_customuser table"""
    
    with connection.cursor() as cursor:
        # Check if role field already exists
        cursor.execute("PRAGMA table_info(accounts_customuser)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'role' in columns:
            print("✅ Role field already exists")
        else:
            # Add role field
            cursor.execute("""
                ALTER TABLE accounts_customuser 
                ADD COLUMN role varchar(20) DEFAULT 'STAFF'
            """)
            print("✅ Added role field")
        
        # Add other new fields if they don't exist
        new_fields = [
            ('phone', 'varchar(20)'),
            ('address', 'text'),
            ('date_of_birth', 'date'),
            ('gender', 'varchar(10)'),
            ('emergency_contact', 'varchar(100)'),
            ('employee_id', 'varchar(20)'),
            ('is_active_staff', 'boolean DEFAULT 1')
        ]
        
        for field_name, field_type in new_fields:
            if field_name not in columns:
                try:
                    cursor.execute(f"""
                        ALTER TABLE accounts_customuser 
                        ADD COLUMN {field_name} {field_type}
                    """)
                    print(f"✅ Added {field_name} field")
                except Exception as e:
                    print(f"⚠️ Could not add {field_name}: {e}")
        
        # Update existing superadmin users to have SUPERADMIN role
        cursor.execute("""
            UPDATE accounts_customuser 
            SET role = 'SUPERADMIN' 
            WHERE is_superadmin = 1 OR is_superuser = 1
        """)
        print("✅ Updated superadmin users with SUPERADMIN role")

if __name__ == "__main__":
    try:
        add_role_field()
        print("✅ CustomUser model fields updated successfully!")
    except Exception as e:
        print(f"❌ Error updating CustomUser fields: {e}")
        import traceback
        traceback.print_exc()
