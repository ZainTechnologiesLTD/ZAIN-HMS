#!/usr/bin/env python
"""
Test script to verify billing models are working
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zain_hms.settings')
django.setup()

from apps.billing.models import ServiceCategory, MedicalService, Invoice
from apps.patients.models import Patient
from django.contrib.auth import get_user_model

User = get_user_model()

def test_billing_models():
    """Test billing models functionality"""
    print("Testing billing models...")
    
    try:
        # Test ServiceCategory
        category_count = ServiceCategory.objects.count()
        print(f"✓ ServiceCategory model works - {category_count} categories found")
        
        # Test MedicalService
        service_count = MedicalService.objects.count()
        print(f"✓ MedicalService model works - {service_count} services found")
        
        # Test Invoice
        invoice_count = Invoice.objects.count()
        print(f"✓ Invoice model works - {invoice_count} invoices found")
        
        # Check if we can create a new category
        test_category, created = ServiceCategory.objects.get_or_create(
            name="Test Category",
            defaults={'description': 'Test category for verification'}
        )
        print(f"✓ ServiceCategory creation works - {'Created new' if created else 'Found existing'} category")
        
        print("\n✅ All billing models are working correctly!")
        print("The billing module should now be accessible without database errors.")
        
    except Exception as e:
        print(f"✗ Error testing billing models: {e}")
        return False
    
    return True

if __name__ == '__main__':
    test_billing_models()
