#!/usr/bin/env python
"""Test script to verify user sazzad can login and access dashboard"""
import os
import django
import sys

# Setup Django environment
sys.path.append('/home/mehedi/Projects/zain_hms')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zain_hms.settings')
django.setup()

from django.test import Client
from django.contrib.auth import authenticate
from apps.accounts.models import CustomUser

def test_sazzad_login():
    print("=== Testing User Sazzad Login ===")
    
    # Check if user exists
    try:
        user = CustomUser.objects.get(username='sazzad')
        print(f"✓ User found: {user.username}")
        print(f"✓ Hospital: {user.hospital.name if user.hospital else 'None'}")
        print(f"✓ Hospital Subdomain: {user.hospital.subdomain if user.hospital else 'None'}")
        print(f"✓ User Active: {user.is_active}")
    except CustomUser.DoesNotExist:
        print("✗ User sazzad not found!")
        return False
    
    # Test authentication
    auth_user = authenticate(username='sazzad', password='Sazzad@123456789')
    if auth_user:
        print("✓ Authentication successful")
    else:
        print("✗ Authentication failed")
        return False
    
    # Test login via client
    client = Client()
    response = client.post('/accounts/login/', {
        'username': 'sazzad',
        'password': 'Sazzad@123456789',
    }, follow=True)
    
    print(f"✓ Login response status: {response.status_code}")
    print(f"✓ Final URL after login: {response.redirect_chain[-1][0] if response.redirect_chain else 'No redirect'}")
    
    # Test dashboard access
    dashboard_response = client.get('/dashboard/')
    print(f"✓ Dashboard access status: {dashboard_response.status_code}")
    
    if dashboard_response.status_code == 200:
        print("✅ SUCCESS: User sazzad can login and access dashboard!")
        return True
    elif dashboard_response.status_code == 302:
        print(f"⚠ Dashboard redirected to: {dashboard_response.url}")
        return False
    else:
        print(f"✗ Dashboard access failed with status {dashboard_response.status_code}")
        return False

if __name__ == "__main__":
    success = test_sazzad_login()
    exit(0 if success else 1)
