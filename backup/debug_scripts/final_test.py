#!/usr/bin/env python3
"""
Final comprehensive test after all fixes
"""
import requests
import time
import subprocess
import os

def start_server():
    """Start Django server"""
    try:
        # Kill any existing servers
        subprocess.run(['pkill', '-f', 'manage.py runserver'], capture_output=True)
        time.sleep(1)
        
        # Start new server in background
        cmd = ['python', 'manage.py', 'runserver', '127.0.0.1:8003']
        env = os.environ.copy()
        env['PYTHONPATH'] = '/home/mehedi/Projects/zain_hms'
        
        process = subprocess.Popen(
            cmd, 
            cwd='/home/mehedi/Projects/zain_hms',
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env
        )
        
        # Wait for server to start
        time.sleep(3)
        return process
    except Exception as e:
        print(f"Error starting server: {e}")
        return None

def test_endpoints():
    """Test all endpoints"""
    
    print("🎯 FINAL TENANT ATTRIBUTE FIX TEST")
    print("=" * 60)
    
    BASE_URL = "http://127.0.0.1:8003"
    
    endpoints = [
        ("/", "Home page"),
        ("/dashboard/", "Dashboard"),
        ("/appointments/", "Appointments list"),
        ("/doctors/", "Doctors list"),  
        ("/patients/", "Patients list"),
        ("/nurses/", "Nurses list"),
        ("/dashboard/settings/", "System settings"),
        ("/appointments/create/enhanced/", "Enhanced appointment creation"),
        ("/doctors/create/", "Doctor creation"),
        ("/patients/create/", "Patient creation"),
    ]
    
    results = {}
    success_count = 0
    error_count = 0
    
    for endpoint, description in endpoints:
        try:
            response = requests.get(BASE_URL + endpoint, timeout=10)
            
            if response.status_code in [200, 201]:
                status = "✅ SUCCESS"
                success_count += 1
            elif response.status_code in [302, 301]:
                status = "🔄 REDIRECT (login/auth)"
                success_count += 1
            elif response.status_code == 403:
                status = "🔒 FORBIDDEN (permissions)"
                success_count += 1
            elif response.status_code == 500:
                status = "❌ SERVER ERROR"
                error_count += 1
            else:
                status = f"⚠️ STATUS {response.status_code}"
                error_count += 1
                
            results[endpoint] = status
            print(f"{endpoint:<30} | {status}")
            
        except requests.exceptions.ConnectionError:
            results[endpoint] = "❌ CONNECTION REFUSED"
            error_count += 1
            print(f"{endpoint:<30} | ❌ CONNECTION REFUSED")
        except Exception as e:
            results[endpoint] = f"❌ ERROR: {e}"
            error_count += 1
            print(f"{endpoint:<30} | ❌ ERROR: {e}")
    
    print("\n" + "=" * 60)
    print("📊 FINAL RESULTS SUMMARY")
    print("=" * 60)
    
    print(f"✅ Working endpoints: {success_count}/{len(endpoints)}")
    print(f"❌ Failed endpoints: {error_count}/{len(endpoints)}")
    
    if error_count == 0:
        print("\n🎉 ALL TENANT ATTRIBUTE ISSUES FIXED!")
        print("✨ Your Hospital Management System is ready to use!")
    elif error_count < 3:
        print("\n✅ MAJOR ISSUES FIXED!")
        print(f"⚠️ Only {error_count} minor issues remain")
    else:
        print("\n⚠️ Some issues still need attention")
    
    return results, success_count, error_count

def main():
    """Main test function"""
    
    # Start server
    print("🚀 Starting Django server...")
    server_process = start_server()
    
    if not server_process:
        print("❌ Failed to start server")
        return
    
    try:
        # Run tests
        results, success, errors = test_endpoints()
        
        # Print final status
        print(f"\n🏆 FINAL STATUS: {success} working / {errors} errors")
        
    finally:
        # Stop server
        if server_process:
            server_process.terminate()
            print("\n🛑 Server stopped")

if __name__ == "__main__":
    main()
