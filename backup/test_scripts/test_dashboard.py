#!/usr/bin/env python
"""
Test dashboard functionality to verify that the field errors are resolved.
"""
import os
import sys
import django
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.conf import settings

# Setup Django environment
sys.path.append('/home/mehedi/Projects/zain_hms')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zain_hms.settings')
django.setup()

# Add testserver to ALLOWED_HOSTS
if 'testserver' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append('testserver')

from apps.core.models import Hospital
from apps.patients.models import Patient
from apps.appointments.models import Appointment

User = get_user_model()

def test_dashboard_access():
    """Test that dashboard loads without field errors"""
    client = Client()
    
    # Get or create a test hospital
    hospital = Hospital.objects.first()
    if not hospital:
        hospital = Hospital.objects.create(
            name="Test Hospital",
            code="TH001",
            address="123 Test St",
            phone="555-0123",
            email="test@test.com"
        )
    
    # Get or create a test admin user
    admin_user = User.objects.filter(role='ADMIN', hospital=hospital).first()
    if not admin_user:
        admin_user = User.objects.create_user(
            username='testadmin',
            email='admin@test.com',
            password='testpass123',
            role='ADMIN',
            hospital=hospital,
            first_name='Test',
            last_name='Admin'
        )
    
    # Login the user
    client.login(username='testadmin', password='testpass123')
    
    # Test dashboard access
    print(f"Testing dashboard access for admin user: {admin_user.username}")
    print(f"Hospital: {hospital.name} ({hospital.code})")
    
    try:
        response = client.get('/pt/dashboard/')
        print(f"Dashboard response status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Dashboard loaded successfully!")
            print("✅ No field errors found!")
            return True
        elif response.status_code == 302:
            print(f"Redirect detected to: {response.get('Location', 'Unknown')}")
            return False
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Dashboard access failed with error: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        return False

if __name__ == '__main__':
    print("Testing Dashboard Field Resolution...")
    print("=" * 50)
    success = test_dashboard_access()
    print("=" * 50)
    if success:
        print("🎉 ALL TESTS PASSED! Dashboard field errors are resolved!")
    else:
        print("❌ Tests failed. Please check the error messages above.")
