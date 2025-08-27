#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zain_hms.settings')
django.setup()

from apps.billing.forms import BillCreateForm
from apps.accounts.models import User

def test_form():
    print("Testing BillCreateForm...")
    
    # Get a user to pass to the form
    user = User.objects.first()
    if not user:
        print("ERROR: No users found")
        return
    
    print(f"User: {user}")
    
    # Create the form
    try:
        form = BillCreateForm(user=user)
        print("Form created successfully")
        
        # Check if form fields are properly set
        print("Form fields:")
        for field_name, field in form.fields.items():
            print(f"  {field_name}: {field.label}")
            if hasattr(field, 'choices') and field_name == 'patient':
                print(f"    Patient choices count: {len(field.choices)}")
                for choice in field.choices[:3]:  # Show first 3 choices
                    print(f"      {choice}")
        
        # Test form with minimal valid data
        from datetime import date
        form_data = {
            'patient': '1',  # Will need to use actual patient ID
            'invoice_date': date.today(),
            'due_date': date.today(),
            'payment_terms': 'IMMEDIATE',
            'notes': 'Test bill',
            'discount_percentage': 0
        }
        
        # Get an actual patient ID
        from apps.patients.models import Patient
        patient = Patient.objects.first()
        if patient:
            form_data['patient'] = patient.id
            print(f"Using patient ID: {patient.id}")
        
        bound_form = BillCreateForm(data=form_data, user=user)
        print(f"Form is valid: {bound_form.is_valid()}")
        
        if not bound_form.is_valid():
            print("Form errors:")
            for field, errors in bound_form.errors.items():
                print(f"  {field}: {errors}")
                
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_form()
