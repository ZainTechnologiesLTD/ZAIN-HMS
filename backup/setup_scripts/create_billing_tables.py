#!/usr/bin/env python
"""
Script to manually create billing tables
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zain_hms.settings')
django.setup()

from django.db import connection
from django.core.management.color import no_style
from django.db import models

# Import billing models
from apps.billing.models import ServiceCategory, MedicalService, Invoice, InvoiceItem, Payment, InsuranceClaim

def create_billing_tables():
    """Create billing tables manually"""
    style = no_style()
    
    # Get SQL statements for creating tables
    with connection.schema_editor() as schema_editor:
        # Create ServiceCategory table
        try:
            schema_editor.create_model(ServiceCategory)
            print("✓ Created ServiceCategory table")
        except Exception as e:
            print(f"✗ Failed to create ServiceCategory table: {e}")
        
        # Create MedicalService table
        try:
            schema_editor.create_model(MedicalService)
            print("✓ Created MedicalService table")
        except Exception as e:
            print(f"✗ Failed to create MedicalService table: {e}")
        
        # Create Invoice table
        try:
            schema_editor.create_model(Invoice)
            print("✓ Created Invoice table")
        except Exception as e:
            print(f"✗ Failed to create Invoice table: {e}")
        
        # Create InvoiceItem table
        try:
            schema_editor.create_model(InvoiceItem)
            print("✓ Created InvoiceItem table")
        except Exception as e:
            print(f"✗ Failed to create InvoiceItem table: {e}")
        
        # Create Payment table
        try:
            schema_editor.create_model(Payment)
            print("✓ Created Payment table")
        except Exception as e:
            print(f"✗ Failed to create Payment table: {e}")
        
        # Create InsuranceClaim table
        try:
            schema_editor.create_model(InsuranceClaim)
            print("✓ Created InsuranceClaim table")
        except Exception as e:
            print(f"✗ Failed to create InsuranceClaim table: {e}")

if __name__ == '__main__':
    print("Creating billing tables...")
    create_billing_tables()
    
    # Verify tables were created
    print("\nVerifying tables...")
    with connection.cursor() as cursor:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%billing%' ORDER BY name;")
        tables = cursor.fetchall()
        
        if tables:
            print("Billing tables found:")
            for table in tables:
                print(f"  - {table[0]}")
        else:
            print("No billing tables found")
