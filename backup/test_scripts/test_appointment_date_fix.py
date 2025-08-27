#!/usr/bin/env python3
"""
Test for Appointment date field FieldError fix
Testing fix for: Cannot resolve keyword 'date' into field
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zain_hms.settings')
django.setup()

from apps.appointments.models import Appointment
from apps.accounts.models import Hospital
from django.utils import timezone

def main():
    print("🔍 APPOINTMENT DATE FIELD FIX VERIFICATION")
    print("=" * 60)
    
    print("📅 Testing Appointment Model Query Fix...")
    
    # Test 1: Verify appointment_date field works
    print("\n📊 Testing Appointment.objects.filter(appointment_date=today):")
    try:
        today = timezone.now().date()
        appointments = Appointment.objects.filter(appointment_date=today)
        print(f"✅ SUCCESS: appointment_date field query works - Found {appointments.count()} appointments")
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False
    
    # Test 2: Verify the old 'date' field doesn't exist
    print(f"\n🔍 Verifying 'date' field removal:")
    try:
        # This should fail gracefully
        Appointment.objects.filter(date=today)
        print("❌ WARNING: 'date' field still exists and works - this shouldn't happen")
        return False
    except Exception as e:
        if "Cannot resolve keyword 'date'" in str(e):
            print("✅ SUCCESS: 'date' field properly removed/doesn't exist")
        else:
            print(f"❌ UNEXPECTED ERROR: {str(e)}")
            return False
    
    # Test 3: Test appointment_date__gte (weekly appointments)
    print(f"\n📊 Testing appointment_date__gte query:")
    try:
        week_start = today - timezone.timedelta(days=today.weekday())
        appointments = Appointment.objects.filter(appointment_date__gte=week_start)
        print(f"✅ SUCCESS: appointment_date__gte query works - Found {appointments.count()} appointments this week")
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False
    
    # Test 4: Import the fixed views
    print(f"\n📁 Testing Hospital Selection Views Import:")
    try:
        from apps.accounts.views_hospital_selection import HospitalSelectionView
        print("✅ SUCCESS: Hospital selection views imported without errors")
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False
    
    # Test 5: Check that view uses correct field
    print(f"\n🔍 Verifying views use appointment_date correctly:")
    try:
        with open('/home/mehedi/Projects/zain_hms/apps/accounts/views_hospital_selection.py', 'r') as f:
            content = f.read()
            if 'appointment_date=' in content and ', date=today' not in content and 'date=today)' not in content:
                print("✅ SUCCESS: Views use appointment_date, not date")
            else:
                print("❌ FAILED: Views may still reference Appointment.date")
                return False
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 ALL TESTS PASSED!")
    print("✅ FieldError for Appointment 'date' field is FIXED")
    print("✅ Appointment.objects.filter(date=today) → Appointment.objects.filter(appointment_date=today)")
    print("✅ Hospital selection system ready for production use")
    print(f"✅ {appointments.count()} appointments available for testing")
    
    print("\n🚀 NEXT STEPS:")
    print("   1. Server should now work without FieldError")
    print("   2. Navigate to /auth/hospital-selection/ as SUPERADMIN")
    print("   3. No Appointment date FieldError should occur")
    print("   4. Hospital statistics should display correctly")
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
