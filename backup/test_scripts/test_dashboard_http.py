#!/usr/bin/env python
"""
Test dashboard via URL access
"""
import requests
import time

def test_dashboard_via_url():
    """Test dashboard access via HTTP"""
    print("Testing Dashboard via HTTP...")
    print("=" * 50)
    
    try:
        # Test dashboard URL
        url = 'http://127.0.0.1:8000/pt/dashboard/'
        print(f"Testing URL: {url}")
        
        response = requests.get(url, timeout=10)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Dashboard loaded successfully!")
            print(f"Content length: {len(response.text)} characters")
            
            # Check for error indicators in response
            if 'FieldError' in response.text or 'EmergencyCase' in response.text:
                print("❌ Found error indicators in response!")
                return False
            else:
                print("✅ No error indicators found in response!")
                return True
                
        elif response.status_code == 302:
            print(f"↪️  Redirect to: {response.headers.get('Location', 'Unknown')}")
            print("This is expected for unauthenticated requests")
            return True  # Redirect is OK for auth
            
        else:
            print(f"❌ Unexpected status: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Is it running?")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == '__main__':
    # Give server time to start up
    time.sleep(2)
    success = test_dashboard_via_url()
    print("=" * 50)
    if success:
        print("🎉 Dashboard HTTP test PASSED!")
    else:
        print("❌ Dashboard HTTP test FAILED!")
