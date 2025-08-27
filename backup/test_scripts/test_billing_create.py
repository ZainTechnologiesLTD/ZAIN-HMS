#!/usr/bin/env python3
"""
Test script to verify billing create functionality
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

def test_billing_urls():
    """Test billing URL accessibility"""
    base_url = "http://127.0.0.1:8000"
    
    urls_to_test = [
        ("/billing/", "Billing Dashboard"),
        ("/billing/create/", "Create Bill Page"),
        ("/billing/list/", "Bill List Page"),
    ]
    
    print(f"Testing billing URLs at {datetime.now()}")
    print("=" * 50)
    
    for url, description in urls_to_test:
        try:
            response = requests.get(f"{base_url}{url}", timeout=10)
            status = "✓ PASS" if response.status_code == 200 else f"✗ FAIL ({response.status_code})"
            print(f"{description:<25} {url:<20} {status}")
            
            if response.status_code != 200:
                print(f"  Error details: {response.status_code} - {response.reason}")
                
        except requests.exceptions.RequestException as e:
            print(f"{description:<25} {url:<20} ✗ FAIL (Connection Error)")
            print(f"  Error details: {e}")
    
    print("=" * 50)

if __name__ == "__main__":
    test_billing_urls()
