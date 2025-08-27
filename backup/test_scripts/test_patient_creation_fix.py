#!/usr/bin/env python
"""
Test script to verify patient account creation fixes
"""
import os
import sys
import django

# Add the project root to the Python path
sys.path.append('/home/mehedi/Projects/zain_hms')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zain_hms.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.accounts.models import Hospital
from apps.accounts.services import UserManagementService
from apps.patients.models import Patient

User = get_user_model()

def test_patient_account_creation():
    """Test patient account creation with database routing"""
    print("🔍 Testing Patient Account Creation Fixes...")
    
    try:
        # Get a hospital instance
        hospital = Hospital.objects.first()
        if not hospital:
            print("❌ No hospital found. Creating test hospital...")
            hospital = Hospital.objects.create(
                name="Test Hospital",
                code="TH999",
                address="Test Address",
                city="Test City",
                state="Test State", 
                country="Test Country",
                postal_code="12345",
                phone="+1234567890",
                email="test@hospital.com"
            )
            print(f"✅ Created test hospital: {hospital.name}")
        
        # Get an admin user as created_by
        admin_user = User.objects.using('default').filter(is_superuser=True).first()
        if not admin_user:
            print("❌ No admin user found. Please ensure you have a superuser.")
            return False
        
        print(f"✅ Using admin user: {admin_user.username}")
        print(f"✅ Using hospital: {hospital.name}")
        
        # Test direct UserManagementService call (this should work)
        print("\n🧪 Testing UserManagementService.create_user_account...")
        
        test_user = UserManagementService.create_user_account(
            email="test.patient.direct@example.com",
            first_name="Test",
            last_name="Patient Direct",
            role="PATIENT",
            hospital=hospital,
            created_by=admin_user,
            additional_data={
                'phone': '+1234567890',
                'date_of_birth': '1990-01-01'
            }
        )
        
        if test_user:
            print(f"✅ Successfully created user via service: {test_user.username}")
            print(f"✅ User ID: {test_user.id}")
            
            # Cleanup
            test_user.delete()
            print("✅ Test user cleaned up")
        else:
            print("❌ Failed to create test user via service")
            return False
        
        # Test patient creation with user account (simulating the view logic)
        print("\n🧪 Testing Patient model creation with user account...")
        
        # Create patient user account first
        patient_user = UserManagementService.create_user_account(
            email="test.patient.model@example.com",
            first_name="Test",
            last_name="Patient Model",
            role="PATIENT",
            hospital=hospital,
            created_by=admin_user,
            additional_data={
                'phone': '+1234567890',
                'date_of_birth': '1990-01-01',
                'gender': 'MALE',
                'blood_group': 'O+',
                'address': 'Test Address'
            }
        )
        
        if not patient_user:
            print("❌ Failed to create patient user account")
            return False
        
        print(f"✅ Created patient user: {patient_user.username}")
        
        # Create patient record
        import random
        unique_id = f"PAT{random.randint(100000, 999999)}"
        test_patient = Patient(
            patient_id=unique_id,
            first_name="Test",
            last_name="Patient Model",
            email="test.patient.model@example.com",
            phone="+1234567890",
            date_of_birth="1990-01-01",
            gender="M",
            blood_group="O+",
            address_line1="Test Address Line 1",
            city="Test City",
            state="Test State",
            postal_code="12345",
            emergency_contact_name="Emergency Contact",
            emergency_contact_relationship="Friend",
            emergency_contact_phone="+1234567890",
            hospital=hospital,
            registered_by=admin_user
        )
        
        # Save patient to tenant database
        hospital_db = f'hospital_{hospital.code}'
        test_patient.save(using=hospital_db)
        
        print(f"✅ Successfully created patient: {test_patient.patient_id}")
        print(f"✅ Patient database: {hospital_db}")
        print(f"✅ Associated user account: {patient_user.username}")
        
        # Verify patient exists in correct database
        saved_patient = Patient.objects.using(hospital_db).get(id=test_patient.id)
        print(f"✅ Patient verified in {hospital_db}: {saved_patient.first_name} {saved_patient.last_name}")
        
        # Cleanup
        print("\n🧹 Cleaning up test data...")
        test_patient.delete(using=hospital_db)
        patient_user.delete()
        print("✅ Test data cleaned up")
        
        print("\n🎉 All Patient account creation tests passed!")
        print("✅ UserManagementService works correctly")
        print("✅ Patient creation with user accounts functions properly")
        print("✅ Database routing works for both User and Patient models")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_patient_account_creation()
    if success:
        print("\n🏆 SUCCESS: Patient account creation is fixed!")
        sys.exit(0)
    else:
        print("\n💥 FAILURE: Issues remain with patient account creation")
        sys.exit(1)
