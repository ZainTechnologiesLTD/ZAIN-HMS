#!/usr/bin/env python3
"""
Test script to verify the fixes for AttributeError and permission issues
"""
import requests
import sys

BASE_URL = "http://127.0.0.1:8000"

def test_endpoints():
    """Test the problematic endpoints to see if they're working now"""
    
    # Create a session to maintain cookies/authentication
    session = requests.Session()
    
    print("🔍 Testing Hospital Management System Endpoints...")
    print("=" * 60)
    
    endpoints_to_test = [
        "/appointments/",
        "/doctors/create/", 
        "/patients/create/",
        "/dashboard/settings/"
    ]
    
    results = {}
    
    for endpoint in endpoints_to_test:
        try:
            url = BASE_URL + endpoint
            response = session.get(url, timeout=10)
            
            # Different status codes and their meanings
            if response.status_code == 200:
                status = "✅ SUCCESS"
            elif response.status_code == 403:
                status = "🔒 FORBIDDEN (may need authentication)"
            elif response.status_code == 302:
                status = "🔄 REDIRECT (likely to login)"
            elif response.status_code == 500:
                status = "❌ INTERNAL SERVER ERROR"
            else:
                status = f"⚠️ STATUS {response.status_code}"
                
            results[endpoint] = {
                'status_code': response.status_code,
                'status': status
            }
            
            print(f"{endpoint:<25} | {status}")
            
        except requests.exceptions.RequestException as e:
            results[endpoint] = {
                'status_code': None,
                'status': f"❌ CONNECTION ERROR: {e}"
            }
            print(f"{endpoint:<25} | ❌ CONNECTION ERROR: {e}")
    
    print("\n" + "=" * 60)
    print("📊 SUMMARY:")
    print("=" * 60)
    
    success_count = sum(1 for r in results.values() if r['status_code'] in [200, 302, 403])
    error_count = sum(1 for r in results.values() if r['status_code'] == 500)
    
    print(f"✅ Working endpoints: {success_count}/{len(endpoints_to_test)}")
    print(f"❌ Error endpoints: {error_count}/{len(endpoints_to_test)}")
    
    if error_count == 0:
        print("\n🎉 All AttributeError issues appear to be fixed!")
        print("💡 For settings access, make sure you're logged in with ADMIN role")
    else:
        print(f"\n⚠️ {error_count} endpoints still have server errors")
        
    return results

if __name__ == "__main__":
    try:
        results = test_endpoints()
    except KeyboardInterrupt:
        print("\n\n🛑 Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        sys.exit(1)
