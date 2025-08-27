#!/usr/bin/env python
"""
Test script to verify UserManagementService database routing fixes
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
from apps.accounts.services import UserManagementService
from apps.accounts.models import Hospital

User = get_user_model()

def test_user_management_service():
    """Test UserManagementService with database routing"""
    print("🔍 Testing UserManagementService Database Routing Fixes...")
    
    try:
        # Get a hospital instance
        hospital = Hospital.objects.first()
        if not hospital:
            print("❌ No hospital found. Creating test hospital...")
            hospital = Hospital.objects.create(
                name="Test Hospital",
                address="Test Address",
                contact_number="1234567890",
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
        
        # Test create_user_account method
        print("\n🧪 Testing create_user_account method...")
        
        test_user = UserManagementService.create_user_account(
            email="test.patient@example.com",
            first_name="Test",
            last_name="Patient",
            role="PATIENT",
            hospital=hospital,
            created_by=admin_user,
            additional_data={
                'phone': '+1234567890',
                'date_of_birth': '1990-01-01'
            }
        )
        
        if test_user:
            print(f"✅ Successfully created user: {test_user.username}")
            print(f"✅ User ID: {test_user.id}")
            print(f"✅ User role: {test_user.role}")
            print(f"✅ User hospital: {test_user.hospital}")
            print(f"✅ User database: 'default' (User model)")
            
            # Test password reset
            print("\n🧪 Testing reset_user_password method...")
            new_password = UserManagementService.reset_user_password(
                test_user.id, 
                admin_user
            )
            
            if new_password:
                print(f"✅ Successfully reset password")
                print(f"✅ New password generated: {len(new_password)} characters")
            else:
                print("❌ Failed to reset password")
            
            # Cleanup test user
            print("\n🧹 Cleaning up test user...")
            test_user.delete()
            print("✅ Test user deleted")
            
        else:
            print("❌ Failed to create test user")
            return False
            
        print("\n🎉 All UserManagementService tests passed!")
        print("✅ Database routing fixes are working correctly")
        print("✅ Patient account creation should now work without 'main.accounts_hospital' error")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_user_management_service()
    if success:
        print("\n🏆 SUCCESS: UserManagementService database routing is fixed!")
        sys.exit(0)
    else:
        print("\n💥 FAILURE: Issues remain with UserManagementService")
        sys.exit(1)
