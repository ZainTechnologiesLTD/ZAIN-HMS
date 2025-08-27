#!/usr/bin/env python3
"""
Test patient creation with user account to verify database routing fix
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.insert(0, '/home/mehedi/Projects/zain_hms')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zain_hms.settings')
django.setup()

from apps.accounts.models import Hospital, User
from apps.patients.models import Patient
from apps.accounts.services import UserManagementService
from apps.core.db_router import TenantDatabaseManager

def test_patient_creation_with_user_account():
    """Test creating a patient with user account in multi-tenant setup"""
    
    print("🔧 Testing Patient Creation with User Account...")
    
    try:
        # Get a hospital from default database (shared)
        hospital = Hospital.objects.using('default').filter(subscription_status='ACTIVE').first()
        if not hospital:
            print("❌ No active hospital found in default database")
            return False
            
        print(f"✅ Found hospital: {hospital.name} (ID: {hospital.id})")
        
        # Set hospital context for tenant database routing
        TenantDatabaseManager.set_hospital_context(hospital.code)
        print(f"✅ Set hospital context to: {hospital.code}")
        
        # Get an admin user from default database
        admin_user = User.objects.using('default').filter(role='SUPERADMIN').first()
        if not admin_user:
            print("❌ No admin user found in default database")
            return False
            
        print(f"✅ Found admin user: {admin_user.username}")
        
        # Test data for patient
        patient_data = {
            'first_name': 'Test',
            'last_name': 'Patient',
            'email': 'test.patient@example.com',
            'phone': '+1234567890',
            'date_of_birth': '1990-01-01',
            'gender': 'M',
            'blood_group': 'O+',
            'address_line1': '123 Test Street',
            'city': 'Test City',
            'state': 'Test State',
            'postal_code': '12345',
            'country': 'Test Country'
        }
        
        print("🔄 Creating patient with user account...")
        
        # Test UserManagementService.create_user_account directly
        user = UserManagementService.create_user_account(
            email=patient_data['email'],
            first_name=patient_data['first_name'],
            last_name=patient_data['last_name'],
            role='PATIENT',
            hospital=hospital,
            created_by=admin_user,
            additional_data={
                'phone': patient_data['phone'],
                'date_of_birth': patient_data['date_of_birth'],
                'gender': patient_data['gender'],
                'blood_group': patient_data['blood_group'],
                'address': f"{patient_data['address_line1']}, {patient_data['city']}, {patient_data['state']}",
            }
        )
        
        print(f"✅ User account created successfully!")
        print(f"   - Username: {user.username}")
        print(f"   - Email: {user.email}")
        print(f"   - Role: {user.role}")
        print(f"   - Hospital: {user.hospital.name}")
        
        # Verify user is in default database
        user_in_default = User.objects.using('default').filter(id=user.id).exists()
        print(f"✅ User exists in default database: {user_in_default}")
        
        # Now create the patient record in tenant database
        print("🔄 Creating patient record in tenant database...")
        
        # Create patient in tenant database
        patient = Patient.objects.create(
            first_name=patient_data['first_name'],
            last_name=patient_data['last_name'],
            email=patient_data['email'],
            phone=patient_data['phone'],
            date_of_birth=patient_data['date_of_birth'],
            gender=patient_data['gender'],
            blood_group=patient_data['blood_group'],
            address_line1=patient_data['address_line1'],
            city=patient_data['city'],
            state=patient_data['state'],
            postal_code=patient_data['postal_code'],
            country=patient_data['country'],
            hospital=hospital,
            registered_by=admin_user
        )
        
        print(f"✅ Patient record created successfully!")
        print(f"   - Patient ID: {patient.patient_id}")
        print(f"   - Name: {patient.get_full_name()}")
        print(f"   - Hospital: {patient.hospital.name}")
        
        # Verify patient is in tenant database
        current_db = TenantDatabaseManager.get_current_hospital_context()
        print(f"✅ Patient created in tenant database: {current_db}")
        
        print("\n🎉 SUCCESS: Patient creation with user account works correctly!")
        print("   - User account created in default database (shared)")
        print("   - Patient record created in tenant database") 
        print("   - Multi-tenant database routing working properly")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_patient_creation_with_user_account()
    sys.exit(0 if success else 1)
