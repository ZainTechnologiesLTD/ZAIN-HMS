#!/usr/bin/env python3

import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zain_hms.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from apps.doctors.views import DoctorListView
from apps.nurses.views import NurseListView
from apps.accounts.models import Hospital

def test_direct_view_access():
    print("🧪 Testing direct view access...")
    
    # Get the user
    User = get_user_model()
    user = User.objects.get(username='dmc_admin')
    
    # Create a mock request
    factory = RequestFactory()
    request = factory.get('/pt/doctors/')
    request.user = user
    
    # Test DoctorListView
    try:
        view = DoctorListView()
        view.request = request
        
        # Test filtering
        from apps.doctors.models import Doctor
        queryset = view.filter_by_hospital(Doctor.objects.all())
        
        print(f"✅ Doctor queryset filtering works: {queryset.count()} doctors found")
        print("✅ No database routing errors!")
        
    except Exception as e:
        print(f"❌ Doctor view error: {e}")
        return False
    
    # Test NurseListView
    try:
        view = NurseListView()
        view.request = request
        
        # Test filtering
        from apps.nurses.models import Nurse
        queryset = view.filter_by_hospital(Nurse.objects.all())
        
        print(f"✅ Nurse queryset filtering works: {queryset.count()} nurses found")
        print("✅ No database routing errors!")
        
    except Exception as e:
        print(f"❌ Nurse view error: {e}")
        return False
    
    print("\n🎉 Direct view access test completed successfully!")
    return True

if __name__ == '__main__':
    test_direct_view_access()
