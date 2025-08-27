#!/usr/bin/env python3
"""
Debug the exact location of the database table error
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
import traceback

def debug_patient_creation_error():
    """Debug exactly where the table error occurs"""
    
    print("🔍 Debugging Patient Creation Error...")
    
    try:
        # Get a hospital from default database (shared)
        print("Step 1: Getting hospital from default database...")
        hospital = Hospital.objects.using('default').filter(subscription_status='ACTIVE').first()
        if not hospital:
            print("❌ No active hospital found in default database")
            return False
            
        print(f"✅ Found hospital: {hospital.name} (ID: {hospital.id})")
        
        # Set hospital context to simulate web interface
        print("Step 2: Setting hospital context...")
        TenantDatabaseManager.set_hospital_context(hospital.code)
        current_context = TenantDatabaseManager.get_current_hospital_context()
        print(f"✅ Hospital context set to: {current_context}")
        
        # Get an admin user from default database
        print("Step 3: Getting admin user...")
        admin_user = User.objects.using('default').filter(role='SUPERADMIN').first()
        if not admin_user:
            print("❌ No admin user found in default database")
            return False
            
        print(f"✅ Found admin user: {admin_user.username}")
        
        # Test data for patient
        patient_data = {
            'first_name': 'Debug',
            'last_name': 'Patient',
            'email': 'debug.patient@example.com',
            'phone': '+1234567892',
            'date_of_birth': '1990-01-01',
            'gender': 'M',
            'blood_group': 'O+',
            'address_line1': '123 Debug Street',
            'city': 'Debug City',
            'state': 'Debug State',
            'postal_code': '12345',
            'country': 'Debug Country'
        }
        
        print("Step 4: Testing UserManagementService.create_user_account...")
        
        # Enable detailed debugging
        import logging
        logging.basicConfig(level=logging.DEBUG)
        
        try:
            print("Step 4a: Before creating user account...")
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
            print(f"✅ User account created: {user.username}")
            
        except Exception as user_error:
            print(f"❌ ERROR in UserManagementService.create_user_account:")
            print(f"   Error: {str(user_error)}")
            print("   Traceback:")
            traceback.print_exc()
            
            # Check what database operations are happening
            print(f"\n🔍 Current hospital context during error: {TenantDatabaseManager.get_current_hospital_context()}")
            
            # Try to identify the exact line causing the issue
            return False
        
        print("\n🎉 DEBUG SUCCESS: No database table errors found!")
        return True
        
    except Exception as e:
        print(f"❌ GENERAL ERROR: {str(e)}")
        traceback.print_exc()
        return False
    finally:
        # Clean up hospital context
        TenantDatabaseManager.set_hospital_context(None)

if __name__ == "__main__":
    success = debug_patient_creation_error()
    sys.exit(0 if success else 1)
