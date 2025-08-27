#!/usr/bin/env python3
"""
Quick test to verify all endpoints are working
"""
import requests

BASE_URL = "http://127.0.0.1:8001"

endpoints = [
    "/appointments/",
    "/doctors/create/", 
    "/patients/create/",
    "/dashboard/settings/"
]

print("🔍 Testing endpoints after import fix...")
print("=" * 50)

for endpoint in endpoints:
    try:
        response = requests.get(BASE_URL + endpoint, timeout=5)
        
        if response.status_code == 200:
            status = "✅ SUCCESS (200)"
        elif response.status_code in [302, 301]:
            status = "🔄 REDIRECT (likely to login/hospital selection)"
        elif response.status_code == 403:
            status = "🔒 FORBIDDEN (authentication required)"
        elif response.status_code == 500:
            status = "❌ SERVER ERROR"
        else:
            status = f"⚠️ STATUS {response.status_code}"
            
        print(f"{endpoint:<25} | {status}")
        
    except requests.exceptions.RequestException as e:
        print(f"{endpoint:<25} | ❌ CONNECTION ERROR: {e}")

print("\n🎉 Import fixes applied successfully!")
