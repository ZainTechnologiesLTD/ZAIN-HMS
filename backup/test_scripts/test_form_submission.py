#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zain_hms.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from apps.accounts.models import Hospital
from apps.patients.models import Patient
from datetime import date

def test_form_submission():
    print("Testing form submission via test client...")
    
    # Create a test client
    client = Client()
    
    # Get or create a user
    User = get_user_model()
    try:
        user = User.objects.get(username='admin')
    except User.DoesNotExist:
        print("Admin user not found, creating one...")
        user = User.objects.create_user('admin', 'admin@test.com', 'admin123')
    
    # Associate user with a hospital
    hospital = Hospital.objects.first()
    if hospital:
        user.hospital = hospital
        user.save()
    
    # Log in the user
    client.login(username='admin', password='admin123')
    
    # Get the create bill page
    response = client.get('/billing/create/')
    print(f"GET /billing/create/ status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"Error accessing create page: {response.content}")
        return
    
    # Get a patient
    patient = Patient.objects.first()
    if not patient:
        print("No patients found")
        return
    
    # Submit form data
    form_data = {
        'patient': str(patient.id),
        'invoice_date': date.today().isoformat(),
        'due_date': date.today().isoformat(),
        'payment_terms': 'IMMEDIATE',
        'notes': 'Test bill submission',
        'discount_percentage': '0'
    }
    
    print(f"Submitting form data: {form_data}")
    
    response = client.post('/billing/create/', data=form_data)
    print(f"POST /billing/create/ status: {response.status_code}")
    
    if response.status_code == 302:
        print(f"Redirect to: {response.url}")
        print("Form submission successful!")
    elif response.status_code == 200:
        print("Form submission returned to same page - likely validation errors")
        # Check for form errors in the response
        if b'error' in response.content.lower():
            print("Response contains errors")
        print(f"Response content preview: {response.content[:500]}")
    else:
        print(f"Unexpected status code: {response.status_code}")
        print(f"Response: {response.content}")

if __name__ == "__main__":
    test_form_submission()
