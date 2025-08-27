#!/usr/bin/env python3
"""
Test script to verify patient creation with user account works in live environment
"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.insert(0, '/home/mehedi/Projects/zain_hms')

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zain_hms.settings')
django.setup()

from apps.patients.models import Patient
from apps.accounts.models import Hospital, User
from apps.accounts.services import UserManagementService
from apps.core.db_router import TenantDatabaseManager
from django.db import transaction
import traceback

def test_live_patient_creation():
    """Test patient creation with user account in live environment"""
    print("🧪 Testing live patient creation with user account...")
    
    try:
        # Get a test hospital
        hospital = Hospital.objects.filter(subscription_status='ACTIVE').first()
        if not hospital:
            print("❌ No active hospital found!")
            return False
            
        print(f"✅ Found test hospital: {hospital.name} (ID: {hospital.id})")
        
        # Set hospital context
        TenantDatabaseManager.set_hospital_context(hospital.code)
        print(f"✅ Set hospital context to: {hospital.code}")
        
        # Test data
        test_patient_data = {
            'first_name': 'Live',
            'last_name': 'Test',
            'email': 'livetest@hospital.com',
            'phone': '1234567890',
            'date_of_birth': '1990-01-01',
            'gender': 'MALE',
            'address': '123 Test Street',
            'emergency_contact_name': 'Emergency Contact',
            'emergency_contact_phone': '0987654321'
        }
        
        print(f"✅ Test patient data: {test_patient_data}")
        
        # Create patient with user account
        print("🔄 Creating patient with user account using UserManagementService...")
        
        # Get an admin user for created_by
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            print("⚠️ Creating temporary admin user for test...")
            admin_user = User.objects.create_user(
                username='test_admin',
                email='admin@test.com',
                is_superuser=True,
                is_staff=True
            )
        
        user = UserManagementService.create_user_account(
            email=test_patient_data['email'],
            first_name=test_patient_data['first_name'],
            last_name=test_patient_data['last_name'],
            role='PATIENT',
            hospital=hospital,
            created_by=admin_user,
            additional_data={'phone': test_patient_data['phone']}
        )
        
        print(f"✅ User account created: {user}")
        
        # Create patient record
        print("🔄 Creating patient record...")
        
        # Use hospital-specific database for patient
        using_db = f'hospital_{hospital.code}'
        patient = Patient.objects.using(using_db).create(
            hospital=hospital,
            first_name=test_patient_data['first_name'],
            last_name=test_patient_data['last_name'],
            email=test_patient_data['email'],
            phone=test_patient_data['phone'],
            date_of_birth=test_patient_data['date_of_birth'],
            gender=test_patient_data['gender'][0],  # Use first letter
            address_line1=test_patient_data['address'],
            city='Test City',
            state='Test State',
            postal_code='12345',
            emergency_contact_name=test_patient_data['emergency_contact_name'],
            emergency_contact_relationship='Family',
            emergency_contact_phone=test_patient_data['emergency_contact_phone'],
            registered_by=user
        )
        
        print(f"✅ Patient created: {patient.id} - {patient.first_name} {patient.last_name}")
        
        # Verify user exists in default database
        user_check = User.objects.using('default').filter(email=test_patient_data['email']).first()
        print(f"✅ User verification in default DB: {user_check.username if user_check else 'NOT FOUND'}")
        
        # Verify patient exists in hospital database
        patient_check = Patient.objects.using(using_db).filter(email=test_patient_data['email']).first()
        print(f"✅ Patient verification in hospital DB: {patient_check.id if patient_check else 'NOT FOUND'}")
        
        print("🎉 SUCCESS: Live patient creation with user account works!")
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        print(f"📊 Exception type: {type(e).__name__}")
        print(f"📋 Traceback:")
        traceback.print_exc()
        return False
    
    finally:
        # Clean up context
        TenantDatabaseManager.set_hospital_context(None)
        print("🧹 Cleaned up hospital context")

if __name__ == "__main__":
    success = test_live_patient_creation()
    sys.exit(0 if success else 1)
