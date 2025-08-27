#!/usr/bin/env python3

import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zain_hms.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.radiology.forms import RadiologyOrderForm

def debug_radiology_form():
    print("🔍 Debugging RadiologyOrderForm...")
    
    # Get the user
    User = get_user_model()
    user = User.objects.get(username='dmc_admin')
    hospital = user.hospital
    
    print(f"✅ User found: {user.username} at {hospital.name}")
    print(f"✅ Hospital ID: {hospital.id} (type: {type(hospital.id)})")
    
    try:
        # Test the ORM query directly
        from apps.accounts.models import User
        
        hospital_user_ids = list(User.objects.using('default').filter(
            hospital=hospital
        ).values_list('id', flat=True))
        
        print(f"✅ ORM query works. Found {len(hospital_user_ids)} users")
        
        # Now test the form
        form = RadiologyOrderForm(hospital=hospital)
        print("✅ RadiologyOrderForm created successfully!")
        
        # Test accessing the queryset
        doctor_choices = list(form.fields['ordering_doctor'].queryset)
        print(f"✅ Doctor choices loaded: {len(doctor_choices)} doctors")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    debug_radiology_form()
