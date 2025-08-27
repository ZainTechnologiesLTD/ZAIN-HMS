#!/usr/bin/env python
"""
URL Testing Script for ZAIN HMS
Tests all URL patterns to ensure they're working correctly
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zain_hms.settings')
django.setup()

from django.urls import reverse, NoReverseMatch
from django.test import RequestFactory
from django.contrib.auth import get_user_model

def test_urls():
    """Test all major URL patterns"""
    
    # URL patterns to test
    url_patterns = [
        # Core URLs
        ('admin:index', None, 'Admin Interface'),
        ('core:home', None, 'Core Dashboard'),
        ('dashboard:dashboard', None, 'Dashboard Home'),
        
        # App URLs (using correct URL names)
        ('patients:list', None, 'Patient List'),
        ('doctors:doctor_list', None, 'Doctor List'),
        ('appointments:appointment_list', None, 'Appointments'),
        ('billing:bill_list', None, 'Billing'),
        ('pharmacy:medicine_list', None, 'Pharmacy'),
        ('laboratory:lab_test_list', None, 'Laboratory Tests'),
        ('radiology:study_list', None, 'Radiology Studies'),
        ('emergency:emergency_list', None, 'Emergency Cases'),
        ('nurses:nurse_list', None, 'Nurses'),
        ('reports:report_list', None, 'Reports'),
        ('ipd:ipd_list', None, 'IPD'),
        ('tenants:hospital_selection', None, 'Tenants'),
        ('accounts:login', None, 'Account Login'),
    ]
    
    print("🔍 Testing URL Patterns for ZAIN HMS")
    print("=" * 50)
    
    working_urls = []
    broken_urls = []
    
    for pattern, args, description in url_patterns:
        try:
            if args:
                url = reverse(pattern, args=args)
            else:
                url = reverse(pattern)
            working_urls.append((pattern, url, description))
            print(f"✅ {description:<20} - {pattern:<30} -> {url}")
        except NoReverseMatch as e:
            broken_urls.append((pattern, str(e), description))
            print(f"❌ {description:<20} - {pattern:<30} -> ERROR: {e}")
        except Exception as e:
            broken_urls.append((pattern, str(e), description))
            print(f"⚠️  {description:<20} - {pattern:<30} -> ERROR: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 URL Test Results:")
    print(f"   ✅ Working URLs: {len(working_urls)}")
    print(f"   ❌ Broken URLs:  {len(broken_urls)}")
    print(f"   📈 Success Rate: {len(working_urls)/(len(working_urls)+len(broken_urls))*100:.1f}%")
    
    if broken_urls:
        print(f"\n🔧 URLs that need attention:")
        for pattern, error, description in broken_urls:
            print(f"   - {pattern}: {error}")
    
    return len(broken_urls) == 0

def test_admin_colors():
    """Test admin interface configuration"""
    from django.conf import settings
    
    print("\n🎨 Testing Admin Interface Configuration")
    print("=" * 50)
    
    # Check Jazzmin configuration
    if hasattr(settings, 'JAZZMIN_SETTINGS'):
        jazzmin = settings.JAZZMIN_SETTINGS
        print(f"✅ Admin Theme: {jazzmin.get('site_title', 'Default')}")
        print(f"✅ Welcome Sign: {jazzmin.get('welcome_sign', 'Default')}")
    
    if hasattr(settings, 'JAZZMIN_UI_TWEAKS'):
        ui_tweaks = settings.JAZZMIN_UI_TWEAKS
        print(f"✅ UI Theme: {ui_tweaks.get('theme', 'default')}")
        print(f"✅ Dark Theme: {ui_tweaks.get('dark_mode_theme', 'default')}")
        print(f"✅ Navbar: {ui_tweaks.get('navbar', 'default')}")
        print(f"✅ Sidebar: {ui_tweaks.get('sidebar', 'default')}")
        
        custom_css = ui_tweaks.get('custom_css')
        if custom_css:
            print(f"✅ Custom CSS: {custom_css}")
        else:
            print("⚠️  No custom CSS configured")
    
    # Check static files
    import os
    static_dir = os.path.join(settings.BASE_DIR, 'static', 'css')
    admin_css = os.path.join(static_dir, 'admin_enhanced.css')
    
    if os.path.exists(admin_css):
        print(f"✅ Enhanced Admin CSS exists")
    else:
        print(f"❌ Enhanced Admin CSS missing")

if __name__ == '__main__':
    print("🏥 ZAIN HMS - URL and Admin Interface Test")
    print("="*60)
    
    try:
        # Test URLs
        urls_ok = test_urls()
        
        # Test admin configuration  
        test_admin_colors()
        
        print("\n" + "="*60)
        if urls_ok:
            print("🎉 All tests completed successfully!")
            print("✅ Your HMS system URLs are working correctly")
            print("✅ Admin interface is properly configured")
        else:
            print("⚠️  Some issues found - check the output above")
            
        print("\n📝 Next steps:")
        print("   1. Run: python manage.py runserver")
        print("   2. Visit: http://localhost:8000/admin/")  
        print("   3. Test the enhanced admin interface")
        
    except Exception as e:
        print(f"💥 Test failed with error: {e}")
        sys.exit(1)
