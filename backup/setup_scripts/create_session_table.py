#!/usr/bin/env python3
"""
Script to manually create the django_session table
"""
import os
import django
import sqlite3

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zain_hms.settings')
django.setup()

from django.db import connection

def create_session_table():
    """Create the django_session table manually"""
    
    with connection.cursor() as cursor:
        # Check if table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='django_session'
        """)
        
        if cursor.fetchone():
            print("django_session table already exists")
            return
        
        # Create the table with the correct schema
        cursor.execute("""
            CREATE TABLE django_session (
                session_key varchar(40) NOT NULL PRIMARY KEY,
                session_data text NOT NULL,
                expire_date datetime NOT NULL
            )
        """)
        
        # Create index for performance
        cursor.execute("""
            CREATE INDEX django_session_expire_date_a5c62663 
            ON django_session (expire_date)
        """)
        
        print("✅ Successfully created django_session table")

if __name__ == "__main__":
    try:
        create_session_table()
        print("✅ Session table setup completed successfully!")
    except Exception as e:
        print(f"❌ Error creating session table: {e}")
        import traceback
        traceback.print_exc()
