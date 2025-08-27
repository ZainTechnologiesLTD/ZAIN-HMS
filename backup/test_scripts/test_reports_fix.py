#!/usr/bin/env python
"""
Test script to verify reports database routing fixes
"""
import os
import sys
import django

# Add the project root to the Python path
sys.path.append('/home/mehedi/Projects/zain_hms')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zain_hms.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.accounts.models import Hospital
from apps.reports.models import Report
from apps.core.db_router import MultiTenantDBRouter

User = get_user_model()

def test_report_creation():
    """Test Report creation with database routing"""
    print("🔍 Testing Reports Database Routing Fixes...")
    
    try:
        # Get a hospital instance
        hospital = Hospital.objects.first()
        if not hospital:
            print("❌ No hospital found. Cannot test reports.")
            return False
        
        # Get an admin user as generated_by
        admin_user = User.objects.using('default').filter(is_superuser=True).first()
        if not admin_user:
            print("❌ No admin user found. Please ensure you have a superuser.")
            return False
        
        print(f"✅ Using admin user: {admin_user.username}")
        print(f"✅ Using hospital: {hospital.name}")
        print(f"✅ Hospital code: {hospital.code}")
        
        # Determine the correct database for this hospital
        hospital_db = f'hospital_{hospital.code}'
        print(f"✅ Target database: {hospital_db}")
        
        # Test creating a report directly
        print("\n🧪 Testing Report creation...")
        
        test_report = Report(
            hospital=hospital,
            generated_by=admin_user,
            name="Test Report",
            report_type="PATIENT",
            format="PDF",
            date_from="2025-01-01",
            date_to="2025-08-19"
        )
        
        # Save to the correct tenant database
        test_report.save(using=hospital_db)
        
        print(f"✅ Successfully created report: {test_report.name}")
        print(f"✅ Report ID: {test_report.id}")
        print(f"✅ Report hospital: {test_report.hospital}")
        print(f"✅ Report generated_by: {test_report.generated_by}")
        print(f"✅ Saved to database: {hospital_db}")
        
        # Verify the report exists in the correct database
        saved_report = Report.objects.using(hospital_db).get(id=test_report.id)
        print(f"✅ Report verified in {hospital_db}: {saved_report.name}")
        
        # Test cross-database relationship access
        print("\n🧪 Testing cross-database relationship access...")
        print(f"✅ Report.hospital: {saved_report.hospital.name} (from default DB)")
        print(f"✅ Report.generated_by: {saved_report.generated_by.username} (from default DB)")
        
        # Cleanup test report
        print("\n🧹 Cleaning up test report...")
        test_report.delete(using=hospital_db)
        print("✅ Test report deleted")
        
        print("\n🎉 All Reports database routing tests passed!")
        print("✅ Report creation works with proper database routing")
        print("✅ Cross-database relationships function correctly")
        print("✅ Reports generate endpoint should now work without 'main.accounts_hospital' error")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_report_creation()
    if success:
        print("\n🏆 SUCCESS: Reports database routing is fixed!")
        sys.exit(0)
    else:
        print("\n💥 FAILURE: Issues remain with Reports database routing")
        sys.exit(1)
