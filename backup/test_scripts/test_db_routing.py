#!/usr/bin/env python3

import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zain_hms.settings')
django.setup()

from django.test import RequestFactory, Client
from django.contrib.auth import get_user_model
from apps.accounts.models import Hospital
from apps.doctors.models import Doctor
from apps.nurses.models import Nurse

def test_database_routing():
    print("🧪 Testing database routing fixes...")
    
    # Get the user
    User = get_user_model()
    user = User.objects.get(username='dmc_admin')
    hospital = user.hospital
    
    print(f"✅ User found: {user.username} at {hospital.name}")
    
    # Test client
    client = Client()
    
    # Login
    login_success = client.login(username='dmc_admin', password='admin123')
    print(f"✅ Login successful: {login_success}")
    
    if not login_success:
        print("❌ Login failed")
        return False
    
    # Test doctors list
    try:
        response = client.get('/pt/doctors/', HTTP_HOST='localhost:8000')
        print(f"✅ Doctors page status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Doctors page loaded successfully!")
        elif response.status_code == 302:
            print(f"ℹ️  Doctors page redirected to: {response.url}")
        else:
            print(f"⚠️  Doctors page returned status: {response.status_code}")
    except Exception as e:
        print(f"❌ Doctors page error: {e}")
        return False
    
    # Test nurses list
    try:
        response = client.get('/pt/nurses/', HTTP_HOST='localhost:8000')
        print(f"✅ Nurses page status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Nurses page loaded successfully!")
        elif response.status_code == 302:
            print(f"ℹ️  Nurses page redirected to: {response.url}")
        else:
            print(f"⚠️  Nurses page returned status: {response.status_code}")
    except Exception as e:
        print(f"❌ Nurses page error: {e}")
        return False
    
    print("\n🎉 Database routing test completed!")
    return True

if __name__ == '__main__':
    test_database_routing()
