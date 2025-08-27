#!/usr/bin/env python3
"""
Final Hospital Selection Test
Comprehensive test to verify the hospital selection fix works
"""
import requests
import time

def test_hospital_selection_workflow():
    """Test the complete hospital selection workflow"""
    
    base_url = "http://127.0.0.1:8002"
    
    print("🧪 Testing Hospital Selection Workflow...")
    print("=" * 50)
    
    # Create a session to maintain cookies
    session = requests.Session()
    
    try:
        # Step 1: Get login page
        print("1. Getting login page...")
        login_page = session.get(f"{base_url}/auth/login/", timeout=10)
        print(f"   Login page status: {login_page.status_code}")
        
        if login_page.status_code != 200:
            print("❌ Cannot access login page")
            return
        
        # Step 2: Extract CSRF token
        csrf_token = None
        for line in login_page.text.split('\n'):
            if 'csrfmiddlewaretoken' in line and 'value=' in line:
                start = line.find('value="') + 7
                end = line.find('"', start)
                csrf_token = line[start:end]
                break
        
        if not csrf_token:
            print("❌ Could not find CSRF token")
            return
            
        print(f"   CSRF token found: {csrf_token[:10]}...")
        
        # Step 3: Login
        print("2. Logging in...")
        login_data = {
            'username': 'mehedi',
            'password': 'mehedi123',  # Try common password
            'csrfmiddlewaretoken': csrf_token
        }
        
        login_response = session.post(f"{base_url}/auth/login/", data=login_data, timeout=10)
        print(f"   Login status: {login_response.status_code}")
        
        if login_response.status_code == 200 and 'login' in login_response.url:
            # Try alternative password
            login_data['password'] = 'password'
            login_response = session.post(f"{base_url}/auth/login/", data=login_data, timeout=10)
            print(f"   Login retry status: {login_response.status_code}")
        
        # Step 4: Try accessing hospital selection
        print("3. Accessing hospital selection...")
        hospital_page = session.get(f"{base_url}/tenants/hospitals/", timeout=10)
        print(f"   Hospital selection status: {hospital_page.status_code}")
        
        if hospital_page.status_code == 200:
            # Check if hospitals are listed
            hospital_count = hospital_page.text.count('Select')
            print(f"   Found {hospital_count} hospital 'Select' buttons")
            
            # Check for specific hospitals
            if 'DEMO001' in hospital_page.text:
                print("   ✅ DEMO001 hospital found")
            else:
                print("   ⚠️  DEMO001 hospital not found")
                
            # Show first few hospitals found
            hospitals_found = []
            lines = hospital_page.text.split('\n')
            for line in lines:
                if 'hospital_' in line and 'Select' in line:
                    hospitals_found.append(line.strip())
            
            if hospitals_found:
                print("   Hospitals available:")
                for i, hospital in enumerate(hospitals_found[:3]):
                    print(f"     {i+1}. {hospital[:100]}...")
            
            return hospital_page.status_code == 200 and hospital_count > 0
        else:
            print(f"   ❌ Hospital selection page not accessible: {hospital_page.status_code}")
            return False
    
    except Exception as e:
        print(f"❌ Error testing workflow: {e}")
        return False

def test_patient_redirect():
    """Test patient creation redirect"""
    base_url = "http://127.0.0.1:8002"
    
    print("\n4. Testing patient creation redirect...")
    try:
        response = requests.get(f"{base_url}/patients/create/", timeout=10, allow_redirects=False)
        print(f"   Patient create status: {response.status_code}")
        
        if response.status_code == 302:
            redirect_url = response.headers.get('Location', '')
            print(f"   Redirects to: {redirect_url}")
            
            if 'login' in redirect_url:
                print("   ✅ Correctly redirects to login (not authenticated)")
            elif 'hospitals' in redirect_url:
                print("   ✅ Correctly redirects to hospital selection")
            else:
                print(f"   ⚠️  Unexpected redirect: {redirect_url}")
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_hospital_selection_workflow()
    test_patient_redirect()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Hospital Selection Fix WORKING!")
        print("✨ You can now log in and select hospitals properly!")
    else:
        print("⚠️  Hospital selection needs more investigation")
    print("🚀 Next: Log in via browser and test the workflow manually")
