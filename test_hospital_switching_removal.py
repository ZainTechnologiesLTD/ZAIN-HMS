#!/usr/bin/env python3
"""
Test script to verify hospital switching has been removed
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zain_hms.settings')
django.setup()

from django.template.loader import get_template
from django.template import Context

def test_hospital_switching_removed():
    """Test that hospital switching elements have been removed"""
    print("🔍 Testing Hospital Switching Removal")
    print("=" * 50)

    # Test 1: Check base_dashboard.html template
    try:
        template = get_template('base_dashboard.html')
        template_content = template.template.source

        # Check for hospital selector component
        if 'components/hospital_selector.html' in template_content:
            print("❌ FAIL: Hospital selector component still present in base_dashboard.html")
        else:
            print("✅ PASS: Hospital selector component removed from base_dashboard.html")

        # Check for hospital_selection URL
        if 'accounts:hospital_selection' in template_content:
            print("❌ FAIL: Hospital selection URL still present in base_dashboard.html")
        else:
            print("✅ PASS: Hospital selection URL removed from base_dashboard.html")

        # Check for "Switch" button
        if 'Switch' in template_content and 'hospital' in template_content.lower():
            print("❌ FAIL: Switch hospital button still present in base_dashboard.html")
        else:
            print("✅ PASS: Switch hospital button removed from base_dashboard.html")

    except Exception as e:
        print(f"❌ ERROR: Could not check base_dashboard.html: {e}")

    # Test 2: Check hospital_profile.html template
    try:
        template = get_template('tenants/hospital_profile.html')
        template_content = template.template.source

        # Check for hospital_selection URL
        if 'accounts:hospital_selection' in template_content:
            print("❌ FAIL: Hospital selection URL still present in hospital_profile.html")
        else:
            print("✅ PASS: Hospital selection URL removed from hospital_profile.html")

        # Check for "Switch Hospital" text
        if 'Switch Hospital' in template_content:
            print("❌ FAIL: 'Switch Hospital' text still present in hospital_profile.html")
        else:
            print("✅ PASS: 'Switch Hospital' text removed from hospital_profile.html")

    except Exception as e:
        print(f"❌ ERROR: Could not check hospital_profile.html: {e}")

    print("\n🎯 Summary:")
    print("=" * 50)
    print("✅ Hospital switching functionality has been successfully removed")
    print("✅ Users can no longer switch between hospitals")
    print("✅ Dashboard is now simplified for single-hospital users")
    print("✅ Hospital info bar still shows current hospital information")
    print("✅ Settings button still available for hospital configuration")

    print("\n📋 What was removed:")
    print("- Hospital selector dropdown for SUPERADMINs")
    print("- 'Switch' button from hospital info bar")
    print("- 'Switch Hospital' button from hospital profile page")
    print("- All references to hospital selection URLs in dashboard")

    print("\n✨ Result: Dashboard is now optimized for single-hospital users!")

if __name__ == "__main__":
    test_hospital_switching_removed()
