#!/usr/bin/env python
"""
Test web form submission for billing
This script tests the actual form submission through web interface
"""
import os
import sys
import django
from django.conf import settings
from django.test import Client, TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

# Add project root to path
sys.path.append('/home/mehedi/Projects/zain_hms')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zain_hms.settings')
django.setup()

from apps.billing.models import Bill
from apps.patients.models import Patient
from apps.accounts.models import Hospital

def test_form_submission():
    print("Testing web form submission...")
    
    # Create a test client
    client = Client()
    
    User = get_user_model()
    
    # Get test user
    try:
        user = User.objects.get(username='babo')
        print(f"Using user: {user.username}")
    except User.DoesNotExist:
        print("User 'babo' not found")
        return
    
    # Login the user
    login_successful = client.login(username='babo', password='test123')
    print(f"Login successful: {login_successful}")
    
    if not login_successful:
        print("Failed to login")
        return
    
    # Get the form page
    form_url = reverse('billing:create')
    print(f"Accessing form URL: {form_url}")
    
    response = client.get(form_url)
    print(f"GET response status: {response.status_code}")
    
    if response.status_code != 200:
        print("Failed to access form page")
        print(f"Response content: {response.content.decode()[:500]}")
        return
    
    # Get a patient for the form
    patient = Patient.objects.filter(hospital=user.hospital).first()
    if not patient:
        print("No patients found")
        return
    
    print(f"Using patient: {patient.name}")
    
    # Prepare form data
    form_data = {
        'patient': str(patient.id),
        'invoice_date': '2024-08-18',
        'due_date': '2024-08-25',
        'payment_terms': 'NET_30',
        'notes': 'Test bill via web form',
        'discount_percentage': '0.00',
    }
    
    # Submit the form
    print("Submitting form...")
    response = client.post(form_url, data=form_data)
    print(f"POST response status: {response.status_code}")
    
    if response.status_code == 302:
        print(f"Form submitted successfully - redirected to: {response.url}")
        
        # Check if bill was created
        latest_bill = Bill.objects.filter(patient=patient).order_by('-created_at').first()
        if latest_bill:
            print(f"Bill created successfully with ID: {latest_bill.id}")
            print(f"Bill notes: {latest_bill.notes}")
        else:
            print("No bill found after submission")
    else:
        print("Form submission failed")
        print(f"Response content: {response.content.decode()[:1000]}")

if __name__ == "__main__":
    test_form_submission()
