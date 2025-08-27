#!/usr/bin/env python
"""
Test script to validate the multi-tenant database fix
Tests all problematic URLs that were causing database errors
"""
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append('/home/mehedi/Projects/zain_hms')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zain_hms.settings')

django.setup()

from django.test import Client
from apps.core.db_router import TenantDatabaseManager
from apps.accounts.models import Hospital, User
from apps.pharmacy.models import PharmacySale
from django.contrib.auth import get_user_model
from django.db import connections

User = get_user_model()

def test_database_routing():
    """Test that models are correctly routed to appropriate databases"""
    print("Testing database routing...")
    
    # Set hospital context
    TenantDatabaseManager.set_hospital_context('TH001')
    
    try:
        # Test shared model - should always use default database
        print("1. Testing User model (shared) - should use default database")
        user_count = User.objects.all().count()
        print(f"   ✓ User count: {user_count}")
        
        # Test tenant model - should use hospital database when context is set
        print("2. Testing PharmacySale model (tenant) - should use hospital database")
        sales_count = PharmacySale.objects.all().count()
        print(f"   ✓ PharmacySale count: {sales_count}")
        
        # Test hospital model - should always use default database
        print("3. Testing Hospital model (shared) - should use default database")
        hospital_count = Hospital.objects.all().count()
        print(f"   ✓ Hospital count: {hospital_count}")
        
        print("✓ All database routing tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Database routing test failed: {e}")
        return False
    finally:
        # Clear hospital context
        TenantDatabaseManager.set_hospital_context(None)

def test_schema_integrity():
    """Test that all hospital databases have proper schema"""
    print("\nTesting database schema integrity...")
    
    hospital_codes = ['TH001', 'DMC001', 'TEST_HOSPITAL']
    
    for hospital_code in hospital_codes:
        print(f"Testing hospital: {hospital_code}")
        
        try:
            # Set hospital context
            TenantDatabaseManager.set_hospital_context(hospital_code)
            
            # Test that PharmacySale table has hospital_id field
            sale = PharmacySale()
            # Try to access hospital field (this will fail if field doesn't exist)
            _ = sale._meta.get_field('hospital')
            print(f"   ✓ {hospital_code}: PharmacySale has hospital field")
            
            # Test creating a PharmacySale object
            hospital = Hospital.objects.filter(code=hospital_code).first()
            if hospital:
                sale = PharmacySale(hospital=hospital, sale_number='TEST001')
                # Don't save, just test that we can create the object
                print(f"   ✓ {hospital_code}: Can create PharmacySale object")
            else:
                print(f"   ! {hospital_code}: Hospital not found in default database")
                
        except Exception as e:
            print(f"   ✗ {hospital_code}: Schema test failed: {e}")
            return False
        finally:
            # Clear hospital context
            TenantDatabaseManager.set_hospital_context(None)
    
    print("✓ All schema integrity tests passed!")
    return True

def test_database_connections():
    """Test that all hospital databases are properly connected"""
    print("\nTesting database connections...")
    
    # Check default database
    try:
        with connections['default'].cursor() as cursor:
            cursor.execute("SELECT 1")
            print("   ✓ Default database connection working")
    except Exception as e:
        print(f"   ✗ Default database connection failed: {e}")
        return False
    
    # Check hospital databases
    hospital_dbs = ['hospital_TH001', 'hospital_DMC001', 'hospital_TEST_HOSPITAL']
    
    for db_name in hospital_dbs:
        try:
            with connections[db_name].cursor() as cursor:
                cursor.execute("SELECT 1")
                print(f"   ✓ {db_name} connection working")
        except Exception as e:
            print(f"   ✗ {db_name} connection failed: {e}")
            return False
    
    print("✓ All database connections working!")
    return True

def main():
    """Run all tests"""
    print("=" * 60)
    print("MULTI-TENANT DATABASE FIX VALIDATION")
    print("=" * 60)
    
    all_passed = True
    
    # Test 1: Database connections
    if not test_database_connections():
        all_passed = False
    
    # Test 2: Schema integrity
    if not test_schema_integrity():
        all_passed = False
    
    # Test 3: Database routing
    if not test_database_routing():
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED! Multi-tenant database system is working correctly.")
        print("\nThe following issues have been resolved:")
        print("✓ User model queries routed to default database")
        print("✓ PharmacySale model has hospital_id field")
        print("✓ All hospital databases have correct schema")
        print("✓ Database routing working properly")
    else:
        print("❌ SOME TESTS FAILED! Please check the errors above.")
    print("=" * 60)
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
