#!/usr/bin/env python
"""
Test form submission using requests library to simulate real browser behavior
"""
import requests
import os
import sys
import django
from django.conf import settings

# Add project root to path
sys.path.append('/home/mehedi/Projects/zain_hms')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zain_hms.settings')
django.setup()

from apps.patients.models import Patient
from apps.billing.models import Bill
from django.contrib.auth import get_user_model

def test_form_with_requests():
    print("Testing form submission with requests library...")
    
    base_url = "http://127.0.0.1:8001"
    session = requests.Session()
    
    User = get_user_model()
    
    # Get test user
    try:
        user = User.objects.get(username='babo')
        print(f"Using user: {user.username}")
    except User.DoesNotExist:
        print("User 'babo' not found")
        return
    
    # First, get the login page to get CSRF token
    login_url = f"{base_url}/auth/login/"
    print(f"Getting login page: {login_url}")
    
    try:
        response = session.get(login_url)
        print(f"Login page status: {response.status_code}")
        
        if response.status_code != 200:
            print("Failed to access login page")
            return
        
        # Extract CSRF token
        csrf_token = None
        if 'csrfmiddlewaretoken' in response.text:
            # Simple extraction - find the csrf token in the form
            import re
            csrf_match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', response.text)
            if csrf_match:
                csrf_token = csrf_match.group(1)
                print(f"Found CSRF token: {csrf_token[:20]}...")
        
        if not csrf_token:
            print("Could not extract CSRF token")
            return
        
        # Login
        login_data = {
            'username': 'babo',
            'password': '12345',
            'csrfmiddlewaretoken': csrf_token,
        }
        
        print("Attempting login...")
        response = session.post(login_url, data=login_data)
        print(f"Login response status: {response.status_code}")
        
        if response.status_code == 302:
            print(f"Login successful - redirected to: {response.headers.get('Location', 'Unknown')}")
        else:
            print("Login failed")
            print(f"Response: {response.text[:500]}")
            return
        
        # Now access the bill create form
        create_url = f"{base_url}/billing/create/"
        print(f"Accessing create form: {create_url}")
        
        response = session.get(create_url)
        print(f"Create form status: {response.status_code}")
        
        if response.status_code != 200:
            print("Failed to access create form")
            print(f"Response: {response.text[:500]}")
            return
        
        # Extract CSRF token from form page
        csrf_match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', response.text)
        if csrf_match:
            csrf_token = csrf_match.group(1)
            print(f"Form CSRF token: {csrf_token[:20]}...")
        else:
            print("Could not extract form CSRF token")
            return
        
        # Get a patient
        patient = Patient.objects.filter(hospital=user.hospital).first()
        if not patient:
            print("No patients found")
            return
        
        print(f"Using patient: {patient.name}")
        
        # Submit the form
        form_data = {
            'patient': str(patient.id),
            'invoice_date': '2024-08-18',
            'due_date': '2024-08-25',
            'payment_terms': 'NET_30',
            'notes': 'Test bill via requests',
            'discount_percentage': '0.00',
            'csrfmiddlewaretoken': csrf_token,
        }
        
        print("Submitting form...")
        response = session.post(create_url, data=form_data)
        print(f"Form submission status: {response.status_code}")
        
        if response.status_code == 302:
            print(f"Form submitted successfully - redirected to: {response.headers.get('Location', 'Unknown')}")
            
            # Check if bill was created
            latest_bill = Bill.objects.filter(patient=patient).order_by('-created_at').first()
            if latest_bill:
                print(f"Bill created successfully with ID: {latest_bill.id}")
                print(f"Bill notes: {latest_bill.notes}")
            else:
                print("No bill found after submission")
        else:
            print("Form submission failed")
            print(f"Response: {response.text[:1000]}")
            
    except requests.exceptions.ConnectionError:
        print("Connection error - is the server running?")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_form_with_requests()
