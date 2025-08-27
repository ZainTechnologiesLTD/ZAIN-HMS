#!/usr/bin/env python3
"""
Test script to verify Create Bill button functionality
"""
import os
import sys
import django
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_dir)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zain_hms.settings')
django.setup()

def test_create_bill_buttons():
    """Test that Create Bill buttons have correct URLs"""
    base_url = "http://127.0.0.1:8000"
    
    try:
        print(f"Testing Create Bill buttons at {datetime.now()}")
        print("=" * 60)
        
        # Get the billing dashboard page
        response = requests.get(f"{base_url}/billing/")
        if response.status_code != 200:
            print(f"✗ FAIL: Cannot access billing dashboard (status: {response.status_code})")
            return
        
        # Parse HTML content
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all links with "Create Bill" text
        create_bill_links = []
        
        # Search for all anchor tags
        for link in soup.find_all('a'):
            link_text = link.get_text(strip=True)
            if 'Create Bill' in link_text or 'Create First Bill' in link_text:
                href = link.get('href', '')
                create_bill_links.append({
                    'text': link_text,
                    'href': href,
                    'element': str(link)
                })
        
        print(f"Found {len(create_bill_links)} Create Bill button(s):")
        print("-" * 60)
        
        for i, link in enumerate(create_bill_links, 1):
            print(f"{i}. Text: '{link['text']}'")
            print(f"   URL: '{link['href']}'")
            
            # Check if URL is correct
            if link['href'] == '/billing/create/':
                print(f"   Status: ✓ CORRECT URL")
            elif link['href'] == '#':
                print(f"   Status: ✗ BROKEN - Links to '#'")
            elif link['href'] == '':
                print(f"   Status: ✗ BROKEN - No URL specified")
            else:
                print(f"   Status: ? UNKNOWN - Unexpected URL")
            
            print(f"   HTML: {link['element'][:100]}...")
            print()
        
        if not create_bill_links:
            print("✗ No Create Bill buttons found on the page!")
        
        print("=" * 60)
        
        # Test the create page directly
        print("Testing Create Bill page accessibility:")
        create_response = requests.get(f"{base_url}/billing/create/")
        if create_response.status_code == 200:
            print("✓ Create Bill page is accessible at /billing/create/")
        else:
            print(f"✗ Create Bill page returned status {create_response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"✗ Connection error: {e}")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")

if __name__ == "__main__":
    test_create_bill_buttons()
