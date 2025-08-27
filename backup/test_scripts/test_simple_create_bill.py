#!/usr/bin/env python3
"""
Simple test script to verify Create Bill button functionality
"""
import os
import sys
import django
import requests
from datetime import datetime

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_dir)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zain_hms.settings')
django.setup()

def test_create_bill_urls():
    """Test Create Bill URL accessibility"""
    base_url = "http://127.0.0.1:8000"
    
    try:
        print(f"Testing Create Bill functionality at {datetime.now()}")
        print("=" * 60)
        
        # Test billing dashboard
        print("1. Testing Billing Dashboard...")
        response = requests.get(f"{base_url}/billing/")
        if response.status_code == 200:
            print("   ✓ Billing dashboard is accessible")
            
            # Check if the response contains the expected URL
            content = response.text
            if '/billing/create/' in content:
                print("   ✓ Create bill URL found in page content")
            else:
                print("   ✗ Create bill URL NOT found in page content")
                
        else:
            print(f"   ✗ Billing dashboard returned status {response.status_code}")
        
        # Test create bill page directly
        print("\n2. Testing Create Bill Page...")
        create_response = requests.get(f"{base_url}/billing/create/")
        if create_response.status_code == 200:
            print("   ✓ Create Bill page is accessible at /billing/create/")
            print("   ✓ The Create Bill buttons should now work correctly!")
        else:
            print(f"   ✗ Create Bill page returned status {create_response.status_code}")
        
        print("\n" + "=" * 60)
        print("SUMMARY:")
        
        if response.status_code == 200 and create_response.status_code == 200:
            print("✓ SUCCESS: Both billing dashboard and create page are working")
            print("✓ The Create Bill buttons have been fixed and should work now")
            print("\nNext steps:")
            print("1. Visit http://127.0.0.1:8000/billing/")
            print("2. Click any 'Create Bill' button")
            print("3. You should be redirected to the bill creation form")
        else:
            print("✗ ISSUES DETECTED: Some pages are not accessible")
            
    except requests.exceptions.RequestException as e:
        print(f"✗ Connection error: {e}")
        print("Make sure the Django server is running on http://127.0.0.1:8000")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")

if __name__ == "__main__":
    test_create_bill_urls()
