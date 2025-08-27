#!/usr/bin/env python3
"""
Utility script to check Patient model fields vs database schema
"""
import os
import sys
import django

# Setup Django
sys.path.append('/home/mehedi/Projects/zain_hms')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zain_hms.settings')
django.setup()

from apps.patients.models import Patient
from django.db import connection

def check_patient_fields():
    """Check Patient model fields vs actual database fields"""
    print("=== PATIENT MODEL vs DATABASE SCHEMA CHECK ===")
    print()
    
    # Get model fields
    model_fields = [field.name for field in Patient._meta.fields]
    print("📋 MODEL FIELDS:")
    for field in sorted(model_fields):
        print(f"  - {field}")
    print()
    
    # Get database table schema
    with connection.cursor() as cursor:
        cursor.execute("PRAGMA table_info(patients_patient)")
        db_columns = cursor.fetchall()
    
    db_field_names = [col[1] for col in db_columns]  # col[1] is the column name
    print("🗄️  DATABASE FIELDS:")
    for field in sorted(db_field_names):
        print(f"  - {field}")
    print()
    
    # Compare
    model_only = set(model_fields) - set(db_field_names)
    db_only = set(db_field_names) - set(model_fields)
    common = set(model_fields) & set(db_field_names)
    
    print("🔍 COMPARISON:")
    print(f"  ✅ Fields in both: {len(common)}")
    print(f"  📝 Model only: {len(model_only)}")
    print(f"  🗄️  Database only: {len(db_only)}")
    print()
    
    if model_only:
        print("📝 FIELDS ONLY IN MODEL:")
        for field in sorted(model_only):
            print(f"  - {field}")
        print()
    
    if db_only:
        print("🗄️  FIELDS ONLY IN DATABASE:")
        for field in sorted(db_only):
            print(f"  - {field}")
        print()
    
    # Check for potential date fields
    print("📅 DATE/TIME RELATED FIELDS:")
    for field in sorted(common):
        if 'date' in field.lower() or 'time' in field.lower() or 'created' in field.lower() or 'updated' in field.lower():
            print(f"  ✅ {field} (available in both)")
    
    for field in sorted(model_only):
        if 'date' in field.lower() or 'time' in field.lower() or 'created' in field.lower() or 'updated' in field.lower():
            print(f"  ❌ {field} (model only - needs migration)")
    
    for field in sorted(db_only):
        if 'date' in field.lower() or 'time' in field.lower() or 'created' in field.lower() or 'updated' in field.lower():
            print(f"  🔧 {field} (database only - model needs update)")
    
    print()
    print("💡 RECOMMENDATIONS:")
    if 'created_at' in db_field_names and 'registration_date' in model_fields:
        print("  - Use 'created_at' field for date queries (exists in database)")
        print("  - Consider running migrations to sync model and database")
    elif 'registration_date' in db_field_names:
        print("  - Use 'registration_date' field for date queries")
    else:
        print("  - No suitable date field found for 'new patients today' queries")

if __name__ == "__main__":
    check_patient_fields()
