#!/usr/bin/env python
"""
Direct test for dashboard functionality using Django management command style.
"""
import os
import sys
import django
from django.test.utils import override_settings

# Setup Django environment
sys.path.append('/home/mehedi/Projects/zain_hms')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zain_hms.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.core.models import Hospital
from apps.core.views import DashboardView
from django.http import HttpRequest
from django.contrib.auth.models import AnonymousUser

User = get_user_model()

def test_dashboard_stats():
    """Test dashboard statistics generation directly"""
    print("Testing Dashboard Statistics Generation...")
    print("=" * 50)
    
    try:
        # Get a test user
        admin_user = User.objects.filter(role='ADMIN').first()
        if not admin_user:
            print("❌ No admin user found")
            return False
            
        hospital = admin_user.hospital
        print(f"Testing with user: {admin_user.username}")
        print(f"Hospital: {hospital.name} ({hospital.code})")
        
        # Create a mock request
        request = HttpRequest()
        request.user = admin_user
        request.hospital = hospital
        
        # Create the view instance
        view = DashboardView()
        view.request = request
        
        # Test the context data generation
        print("Attempting to generate dashboard context...")
        context = view.get_context_data()
        
        print("✅ Dashboard context generated successfully!")
        print(f"Context keys: {list(context.keys())}")
        
        # Check for expected statistics
        expected_stats = [
            'total_patients', 'new_patients_today', 'new_patients_week', 'new_patients_month',
            'total_appointments', 'appointments_today', 'pending_appointments',
            'total_doctors', 'total_nurses', 'total_staff'
        ]
        
        missing_stats = []
        for stat in expected_stats:
            if stat not in context:
                missing_stats.append(stat)
        
        if missing_stats:
            print(f"⚠️  Missing statistics: {missing_stats}")
        else:
            print("✅ All expected statistics are present!")
            
        # Print some sample statistics
        print(f"Total Patients: {context.get('total_patients', 'N/A')}")
        print(f"New Patients Today: {context.get('new_patients_today', 'N/A')}")
        print(f"Total Appointments: {context.get('total_appointments', 'N/A')}")
        print(f"Appointments Today: {context.get('appointments_today', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Dashboard test failed with error: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_dashboard_stats()
    print("=" * 50)
    if success:
        print("🎉 Dashboard statistics test PASSED!")
        print("✅ No field errors found in dashboard generation!")
    else:
        print("❌ Dashboard statistics test FAILED!")
