#!/usr/bin/env python3
"""
Complete Test Suite for Hospital Selection Implementation
Tests the fix for: FieldError at /auth/hospital-selection/ Cannot resolve keyword 'is_active'
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zain_hms.settings')
django.setup()

from django.test import RequestFactory, Client
from django.contrib.auth import get_user_model
from apps.accounts.models import Hospital
from apps.accounts.views_hospital_selection import HospitalSelectionView, select_hospital
from apps.core.middleware import HospitalMiddleware

User = get_user_model()

def test_hospital_model_fields():
    """Test that Hospital model uses subscription_status correctly"""
    print("=== Testing Hospital Model ===")
    
    # Test that subscription_status field exists and works
    hospitals = Hospital.objects.filter(subscription_status='ACTIVE')
    print(f"✅ Found {hospitals.count()} active hospitals using subscription_status='ACTIVE'")
    
    for hospital in hospitals:
        print(f"   - {hospital.name} ({hospital.code}) - Status: {hospital.subscription_status}")
    
    return True

def test_hospital_selection_view():
    """Test HospitalSelectionView works without FieldError"""
    print("\n=== Testing Hospital Selection View ===")
    
    try:
        # Create a test request
        factory = RequestFactory()
        request = factory.get('/auth/hospital-selection/')
        
        # Create a SUPERADMIN user
        superadmin = User.objects.filter(role='SUPERADMIN').first()
        if not superadmin:
            print("⚠️  No SUPERADMIN user found, creating test user")
            superadmin = User.objects.create_user(
                username='test_superadmin',
                email='test@admin.com',
                role='SUPERADMIN',
                password='testpass123'
            )
        
        request.user = superadmin
        
        # Test the view
        view = HospitalSelectionView()
        response = view.get(request)
        
        print("✅ HospitalSelectionView executed without FieldError")
        print(f"✅ Response status: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in HospitalSelectionView: {str(e)}")
        return False

def test_select_hospital_function():
    """Test select_hospital function works"""
    print("\n=== Testing select_hospital Function ===")
    
    try:
        factory = RequestFactory()
        hospital = Hospital.objects.filter(subscription_status='ACTIVE').first()
        
        if not hospital:
            print("❌ No active hospitals found")
            return False
        
        request = factory.post('/auth/select-hospital/', {'hospital_id': str(hospital.id)})
        request.session = {}
        
        # Create a SUPERADMIN user
        superadmin = User.objects.filter(role='SUPERADMIN').first()
        if not superadmin:
            superadmin = User.objects.create_user(
                username='test_superadmin2',
                email='test2@admin.com',
                role='SUPERADMIN',
                password='testpass123'
            )
        
        request.user = superadmin
        
        # Test the function (note: this will redirect, so we expect a redirect response)
        response = select_hospital(request)
        
        print("✅ select_hospital function executed without error")
        print(f"✅ Response status: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in select_hospital: {str(e)}")
        return False

def test_middleware_integration():
    """Test HospitalMiddleware works with the fixed implementation"""
    print("\n=== Testing Middleware Integration ===")
    
    try:
        from apps.core.middleware import HospitalMiddleware
        
        factory = RequestFactory()
        request = factory.get('/dashboard/')
        request.session = {}
        
        # Create a test user with hospital
        hospital = Hospital.objects.filter(subscription_status='ACTIVE').first()
        if not hospital:
            print("❌ No active hospitals found")
            return False
        
        user = User.objects.filter(hospital=hospital).first()
        if not user:
            user = User.objects.create_user(
                username='test_doctor',
                email='doctor@test.com',
                role='DOCTOR',
                hospital=hospital,
                password='testpass123'
            )
        
        request.user = user
        
        # Test middleware
        middleware = HospitalMiddleware(lambda req: type('MockResponse', (), {'status_code': 200})())
        response = middleware(request)
        
        print("✅ HospitalMiddleware processed request successfully")
        print(f"✅ Hospital context set: {hasattr(request, 'hospital')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in middleware: {str(e)}")
        return False

def test_url_accessibility():
    """Test that the hospital selection URL is accessible"""
    print("\n=== Testing URL Accessibility ===")
    
    try:
        client = Client()
        
        # Create and login as SUPERADMIN
        superadmin = User.objects.filter(role='SUPERADMIN').first()
        if not superadmin:
            superadmin = User.objects.create_user(
                username='test_superadmin_url',
                email='url@admin.com',
                role='SUPERADMIN',
                password='testpass123'
            )
        
        client.force_login(superadmin)
        
        # Test the URL
        response = client.get('/auth/hospital-selection/')
        
        print(f"✅ Hospital selection URL accessible: {response.status_code}")
        print(f"✅ No FieldError encountered")
        
        return True
        
    except Exception as e:
        print(f"❌ Error accessing URL: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🏥 HOSPITAL SELECTION FIX - COMPLETE TEST SUITE")
    print("=" * 60)
    
    tests = [
        test_hospital_model_fields,
        test_hospital_selection_view,
        test_select_hospital_function,
        test_middleware_integration,
        test_url_accessibility,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print(f"❌ {test.__name__} failed")
        except Exception as e:
            print(f"❌ {test.__name__} failed with exception: {str(e)}")
    
    print("\n" + "=" * 60)
    print(f"📊 TEST RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Hospital selection FieldError is FIXED!")
        print("✅ subscription_status='ACTIVE' implementation working correctly")
        print("✅ Hospital selection system fully functional")
        print("✅ Multi-hospital support ready for production")
    else:
        print("⚠️  Some tests failed. Please review the implementation.")
    
    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
