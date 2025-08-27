#!/usr/bin/env python3
"""
Test for Hospital Selection URL Fix  
Testing fix for: Reverse for 'select_hospital' with arguments '('0000',)' not found
"""

import os
import sys
import django
import uuid

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zain_hms.settings')
django.setup()

from django.urls import reverse
from apps.accounts.models import Hospital

def main():
    print("🔍 HOSPITAL SELECTION URL FIX VERIFICATION")
    print("=" * 60)
    
    print("🌐 Testing URL Pattern Fix...")
    
    # Test 1: Check that we can reverse the URL with a proper UUID
    print("\n📊 Testing URL reversal with valid UUID:")
    try:
        # Get a real hospital UUID
        hospital = Hospital.objects.filter(subscription_status='ACTIVE').first()
        if not hospital:
            print("❌ No active hospitals found")
            return False
        
        # Test URL reversal with real hospital ID
        url = reverse('accounts:select_hospital', kwargs={'hospital_id': hospital.id})
        print(f"✅ SUCCESS: URL generated: {url}")
        print(f"✅ Hospital ID: {hospital.id}")
        print(f"✅ Hospital Name: {hospital.name}")
        
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False
    
    # Test 2: Verify the old '0000' would fail
    print(f"\n🔍 Verifying '0000' placeholder would fail:")
    try:
        # This should fail because '0000' is not a valid UUID
        url = reverse('accounts:select_hospital', kwargs={'hospital_id': '0000'})
        print("❌ WARNING: '0000' unexpectedly worked - this shouldn't happen")
        return False
    except Exception as e:
        if "not found" in str(e) or "is not a valid UUID" in str(e) or "does not match" in str(e):
            print("✅ SUCCESS: '0000' properly rejected as invalid UUID")
        else:
            print(f"❌ UNEXPECTED ERROR: {str(e)}")
            return False
    
    # Test 3: Test with a properly formatted dummy UUID
    print(f"\n📊 Testing with properly formatted UUID:")
    try:
        # Generate a valid UUID format for testing
        dummy_uuid = str(uuid.uuid4())
        url = reverse('accounts:select_hospital', kwargs={'hospital_id': dummy_uuid})
        print(f"✅ SUCCESS: URL generated with dummy UUID: {url}")
        print(f"✅ Dummy UUID: {dummy_uuid}")
        
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False
    
    # Test 4: Check the template fix
    print(f"\n📁 Verifying template fix:")
    try:
        with open('/home/mehedi/Projects/zain_hms/templates/accounts/hospital_selection.html', 'r') as f:
            content = f.read()
            if "'/auth/select-hospital/' + hospitalId + '/'" in content and "'0000'" not in content:
                print("✅ SUCCESS: Template uses dynamic URL building, not '0000' placeholder")
            else:
                print("❌ FAILED: Template may still contain '0000' placeholder")
                return False
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 ALL TESTS PASSED!")
    print("✅ URL Template Error is FIXED")
    print("✅ Django URL pattern expects proper UUID format")
    print("✅ Template now builds URLs dynamically in JavaScript")
    print("✅ Hospital selection AJAX should work correctly")
    
    print("\n🚀 NEXT STEPS:")
    print("   1. Template no longer uses invalid '0000' placeholder")
    print("   2. JavaScript builds proper URLs with real hospital UUIDs")
    print("   3. Hospital selection should work without URL errors")
    print("   4. AJAX requests should succeed")
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
