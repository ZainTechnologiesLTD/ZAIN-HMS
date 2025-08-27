#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zain_hms.settings')
django.setup()

from apps.billing.models import Invoice, Bill
from apps.patients.models import Patient  
from apps.accounts.models import User, Hospital
from datetime import date

def test_bill_creation():
    print("Testing bill creation...")
    
    # Get test data
    patient = Patient.objects.first()
    user = User.objects.first()
    hospital = Hospital.objects.first()
    
    if not patient:
        print("ERROR: No patients found")
        return
        
    if not user:
        print("ERROR: No users found")
        return
        
    if not hospital:
        print("ERROR: No hospitals found")
        return
    
    print(f"Patient: {patient}")
    print(f"User: {user}")
    print(f"Hospital: {hospital}")
    
    # Try to create a bill
    try:
        bill = Bill.objects.create(
            hospital=hospital,
            patient=patient,
            invoice_date=date.today(),
            due_date=date.today(),
            created_by=user,
            notes="Test bill"
        )
        print(f"SUCCESS: Bill created with ID: {bill.id}")
        print(f"Bill number: {bill.invoice_number}")
        return bill
    except Exception as e:
        print(f"ERROR creating bill: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_bill_creation()
