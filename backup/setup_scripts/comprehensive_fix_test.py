#!/usr/bin/env python3
"""
Comprehensive Fix Test
Tests all previously failing endpoints to verify fixes
"""
import requests
import time

def test_endpoints():
    """Test all major endpoints"""
    
    base_url = "http://127.0.0.1:8001"
    
    endpoints = [
        "/",
        "/dashboard/",
        "/appointments/",
        "/appointments/create/enhanced/",
        "/doctors/",
        "/doctors/create/",
        "/patients/",
        "/patients/create/",
        "/nurses/",
        "/nurses/create/",
        "/dashboard/settings/",
        "/laboratory/",
        "/auth/users/",
    ]
    
    print("🧪 Testing HMS Endpoints After Fixes...")
    print("=" * 50)
    
    working = 0
    errors = 0
    
    for endpoint in endpoints:
        try:
            # Add small delay between requests
            time.sleep(0.5)
            
            response = requests.get(f"{base_url}{endpoint}", timeout=10, allow_redirects=True)
            
            if response.status_code == 200:
                print(f"✅ {endpoint:<30} SUCCESS (200)")
                working += 1
            elif response.status_code in [302, 301]:
                print(f"🔄 {endpoint:<30} REDIRECT ({response.status_code})")
                working += 1
            else:
                print(f"❌ {endpoint:<30} ERROR ({response.status_code})")
                errors += 1
                
        except Exception as e:
            print(f"💥 {endpoint:<30} EXCEPTION: {str(e)[:50]}")
            errors += 1
    
    print("=" * 50)
    print(f"📊 FINAL RESULTS:")
    print(f"   ✅ Working: {working}")
    print(f"   ❌ Errors: {errors}")
    print(f"   📈 Success Rate: {working/(working+errors)*100:.1f}%")
    
    if errors == 0:
        print("\n🎉 ALL FIXES SUCCESSFUL! 🎉")
        print("✨ Your Hospital Management System is fully operational! ✨")
        print("🏆 STATUS: ALL ENDPOINTS WORKING")
    else:
        print(f"\n⚠️  {errors} endpoints still need attention")
        
    return working, errors

if __name__ == "__main__":
    test_endpoints()
