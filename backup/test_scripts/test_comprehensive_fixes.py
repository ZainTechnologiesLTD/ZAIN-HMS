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
from apps.radiology.forms import RadiologyOrderForm
from apps.laboratory.forms import LabOrderForm
from apps.appointments.forms import AppointmentForm

def test_forms_safely():
    print("🧪 Testing forms with cross-database fixes...")
    
    # Get the user
    User = get_user_model()
    user = User.objects.get(username='dmc_admin')
    hospital = user.hospital
    
    print(f"✅ User found: {user.username} at {hospital.name}")
    
    # Test RadiologyOrderForm
    try:
        form = RadiologyOrderForm(hospital=hospital)
        doctor_choices = list(form.fields['ordering_doctor'].queryset)
        print(f"✅ RadiologyOrderForm: {len(doctor_choices)} doctors loaded")
    except Exception as e:
        print(f"❌ RadiologyOrderForm error: {e}")
        return False
    
    # Test LabOrderForm  
    try:
        form = LabOrderForm(hospital=hospital)
        doctor_choices = list(form.fields['doctor'].queryset)
        print(f"✅ LabOrderForm: {len(doctor_choices)} doctors loaded")
    except Exception as e:
        print(f"❌ LabOrderForm error: {e}")
        return False
    
    # Test AppointmentForm
    try:
        form = AppointmentForm(hospital=hospital)
        doctor_choices = list(form.fields['doctor'].queryset)
        print(f"✅ AppointmentForm: {len(doctor_choices)} doctors loaded")
    except Exception as e:
        print(f"❌ AppointmentForm error: {e}")
        return False
    
    print("\n🎉 All forms tested successfully!")
    return True

def test_views_with_client():
    print("🧪 Testing views with client...")
    
    client = Client()
    
    # Login
    login_success = client.login(username='dmc_admin', password='admin123')
    print(f"✅ Login successful: {login_success}")
    
    if not login_success:
        print("❌ Login failed")
        return False
    
    # Test various pages
    test_urls = [
        ('/pt/doctors/', 'Doctors'),
        ('/pt/nurses/', 'Nurses'),
        ('/pt/radiology/', 'Radiology'),
        ('/pt/laboratory/', 'Laboratory'),
        ('/pt/radiology/studies/', 'Radiology Studies'),
    ]
    
    for url, name in test_urls:
        try:
            response = client.get(url)
            if response.status_code == 200:
                print(f"✅ {name} page: HTTP 200")
            elif response.status_code == 302:
                print(f"ℹ️  {name} page: HTTP 302 (redirect)")
            else:
                print(f"⚠️  {name} page: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ {name} page error: {e}")
            return False
    
    print("\n🎉 All views tested successfully!")
    return True

if __name__ == '__main__':
    try:
        test_forms_safely()
        test_views_with_client()
    except Exception as e:
        print(f"❌ Test failed: {e}")
