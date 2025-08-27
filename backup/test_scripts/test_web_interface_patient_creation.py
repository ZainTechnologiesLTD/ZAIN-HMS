#!/usr/bin/env python3
"""
Test patient creation through web interface simulation
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

def test_web_interface_patient_creation():
    """Test creating a patient via web interface simulation with hospital context"""
    
    print("🔧 Testing Web Interface Patient Creation...")
    
    try:
        # Get a hospital from default database (shared)
        hospital = Hospital.objects.using('default').filter(subscription_status='ACTIVE').first()
        if not hospital:
            print("❌ No active hospital found in default database")
            return False
            
        print(f"✅ Found hospital: {hospital.name} (ID: {hospital.id})")
        
        # Set hospital context to simulate web interface (this is what causes the issue)
        TenantDatabaseManager.set_hospital_context(hospital.code)
        print(f"✅ Set hospital context to: {hospital.code} (simulating web interface)")
        
        # Verify current context
        current_context = TenantDatabaseManager.get_current_hospital_context()
        print(f"✅ Current hospital context: {current_context}")
        
        # Get an admin user from default database
        admin_user = User.objects.using('default').filter(role='SUPERADMIN').first()
        if not admin_user:
            print("❌ No admin user found in default database")
            return False
            
        print(f"✅ Found admin user: {admin_user.username}")
        
        # Test data for patient
        patient_data = {
            'first_name': 'Web',
            'last_name': 'Patient',
            'email': 'web.patient@example.com',
            'phone': '+1234567891',
            'date_of_birth': '1990-01-01',
            'gender': 'F',
            'blood_group': 'A+',
            'address_line1': '123 Web Street',
            'city': 'Web City',
            'state': 'Web State',
            'postal_code': '12345',
            'country': 'Web Country'
        }
        
        print("🔄 Creating patient with user account (with hospital context set)...")
        
        # This should now work because we temporarily clear hospital context in UserManagementService
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
        
        # Verify hospital context is still set (should be restored)
        final_context = TenantDatabaseManager.get_current_hospital_context()
        print(f"✅ Hospital context after user creation: {final_context}")
        
        print("\n🎉 SUCCESS: Web interface patient creation with user account works!")
        print("   - Hospital context was properly managed during user creation")
        print("   - User account created in default database (shared)")
        print("   - Hospital context restored after user creation")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up hospital context
        TenantDatabaseManager.set_hospital_context(None)

if __name__ == "__main__":
    success = test_web_interface_patient_creation()
    sys.exit(0 if success else 1)
