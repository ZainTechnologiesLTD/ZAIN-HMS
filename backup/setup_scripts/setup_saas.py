#!/usr/bin/env python3
"""
Multi-Tenant SaaS Hospital Management System Setup Script
This script sets up the entire multi-tenant infrastructure
"""

import os
import sys
import django
from pathlib import Path

# Add the project directory to Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zain_hms.settings')
django.setup()

from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.db import transaction
from apps.accounts.models import Hospital
from apps.core.db_router import TenantDatabaseManager

User = get_user_model()


class SaaSSetup:
    """Setup class for multi-tenant SaaS application"""
    
    def __init__(self):
        self.success_count = 0
        self.error_count = 0
        
    def print_header(self, title):
        """Print formatted header"""
        print("\n" + "=" * 60)
        print(f" {title}")
        print("=" * 60)
        
    def print_step(self, step, description):
        """Print step information"""
        print(f"\n[Step {step}] {description}")
        print("-" * 40)
        
    def print_success(self, message):
        """Print success message"""
        print(f"✅ {message}")
        self.success_count += 1
        
    def print_error(self, message):
        """Print error message"""
        print(f"❌ {message}")
        self.error_count += 1
        
    def print_warning(self, message):
        """Print warning message"""
        print(f"⚠️  {message}")
        
    def run_setup(self):
        """Run the complete setup process"""
        self.print_header("ZAIN HMS - Multi-Tenant SaaS Setup")
        print("Setting up Hospital Management System as a Service...")
        
        try:
            # Step 1: Database Setup
            self.print_step(1, "Setting up main database")
            self.setup_main_database()
            
            # Step 2: Create Super Admin
            self.print_step(2, "Creating Super Administrator")
            self.create_super_admin()
            
            # Step 3: Demo Hospital Setup
            self.print_step(3, "Setting up demo hospital (optional)")
            self.setup_demo_hospital()
            
            # Step 4: Configuration Summary
            self.print_step(4, "Setup Summary")
            self.print_summary()
            
        except KeyboardInterrupt:
            print("\n\n❌ Setup interrupted by user")
            sys.exit(1)
        except Exception as e:
            print(f"\n\n❌ Setup failed with error: {str(e)}")
            sys.exit(1)
    
    def setup_main_database(self):
        """Setup the main database with migrations"""
        try:
            print("Running database migrations...")
            call_command('migrate', verbosity=1)
            self.print_success("Main database setup completed")
            
            print("Creating cache table...")
            call_command('createcachetable', verbosity=0)
            self.print_success("Cache table created")
            
        except Exception as e:
            self.print_error(f"Database setup failed: {str(e)}")
            raise
    
    def create_super_admin(self):
        """Create super administrator"""
        # Check if super admin already exists
        if User.objects.filter(role='SUPERADMIN').exists():
            self.print_warning("Super admin already exists, skipping creation")
            return
            
        print("\nCreating Super Administrator...")
        print("Please provide the following information:")
        
        # Get input from user
        username = input("Username: ").strip()
        if not username:
            username = "superadmin"
            
        email = input("Email: ").strip()
        if not email:
            email = "admin@zainhms.com"
            
        first_name = input("First Name (default: Super): ").strip()
        if not first_name:
            first_name = "Super"
            
        last_name = input("Last Name (default: Admin): ").strip()
        if not last_name:
            last_name = "Admin"
            
        # Password
        import getpass
        while True:
            password = getpass.getpass("Password: ")
            if len(password) >= 8:
                password_confirm = getpass.getpass("Confirm Password: ")
                if password == password_confirm:
                    break
                else:
                    print("Passwords don't match. Please try again.")
            else:
                print("Password must be at least 8 characters long.")
        
        try:
            with transaction.atomic():
                superadmin = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    role='SUPERADMIN',
                    is_staff=True,
                    is_superuser=True,
                    is_active=True,
                    is_approved=True,
                    email_verified=True,
                )
                
            self.print_success(f"Super admin '{username}' created successfully")
            
        except Exception as e:
            self.print_error(f"Failed to create super admin: {str(e)}")
            raise
    
    def setup_demo_hospital(self):
        """Setup a demo hospital for testing"""
        create_demo = input("\nWould you like to create a demo hospital? (y/N): ").strip().lower()
        
        if create_demo not in ['y', 'yes']:
            self.print_warning("Skipping demo hospital creation")
            return
            
        print("\nSetting up demo hospital...")
        
        try:
            with transaction.atomic():
                # Create demo hospital
                demo_hospital = Hospital.objects.create(
                    name="Demo General Hospital",
                    code="DEMO001",
                    email="admin@demo-hospital.com",
                    phone="+1-555-0123",
                    address="123 Healthcare Avenue",
                    city="Demo City",
                    state="Demo State",
                    country="USA",
                    postal_code="12345",
                    subscription_plan="TRIAL",
                    subscription_status="ACTIVE",
                    settings={
                        'timezone': 'UTC',
                        'date_format': 'Y-m-d',
                        'time_format': '24h',
                        'currency': 'USD',
                        'language': 'en',
                        'allow_online_appointments': True,
                        'appointment_reminder': True,
                        'email_notifications': True,
                        'sms_notifications': False,
                    }
                )
                
                self.print_success(f"Demo hospital '{demo_hospital.name}' created")
                
                # Create hospital database
                print("Creating demo hospital database...")
                TenantDatabaseManager.create_hospital_database(demo_hospital.code)
                self.print_success("Demo hospital database created")
                
                # Create admin user for demo hospital
                demo_admin = User.objects.create_user(
                    username="demo_admin",
                    email="admin@demo-hospital.com",
                    password="demo_password",
                    first_name="Demo",
                    last_name="Administrator",
                    hospital=demo_hospital,
                    role="ADMIN",
                    is_staff=True,
                    is_active=True,
                    is_approved=True,
                    email_verified=True,
                    employee_id=f"{demo_hospital.code}-ADM-00001",
                )
                
                self.print_success(f"Demo admin '{demo_admin.username}' created")
                
        except Exception as e:
            self.print_error(f"Failed to create demo hospital: {str(e)}")
            # Don't raise here as this is optional
    
    def print_summary(self):
        """Print setup summary"""
        print(f"\n✅ Setup completed with {self.success_count} successful steps")
        if self.error_count > 0:
            print(f"⚠️  {self.error_count} errors encountered")
        
        print("\n" + "=" * 60)
        print(" SETUP SUMMARY")
        print("=" * 60)
        
        print("\n🎉 Your Multi-Tenant SaaS HMS is ready!")
        
        # Get super admin info
        superadmin = User.objects.filter(role='SUPERADMIN').first()
        if superadmin:
            print(f"\n👤 Super Admin: {superadmin.username} ({superadmin.email})")
        
        # Get demo hospital info
        demo_hospital = Hospital.objects.filter(code='DEMO001').first()
        if demo_hospital:
            demo_admin = demo_hospital.users.filter(role='ADMIN').first()
            print(f"\n🏥 Demo Hospital: {demo_hospital.name}")
            if demo_admin:
                print(f"   Admin: {demo_admin.username} / demo_password")
        
        print("\n📋 Next Steps:")
        print("1. Start the development server: python manage.py runserver")
        print("2. Access Super Admin Dashboard: http://localhost:8000/auth/superadmin/")
        print("3. Access Django Admin: http://localhost:8000/admin/")
        print("4. Create hospitals using management commands or admin interface")
        
        print("\n🔧 Management Commands:")
        print("• Create hospital: python manage.py setup_hospital --help")
        print("• Create super admin: python manage.py create_superadmin --help")
        
        print("\n📖 Documentation:")
        print("• Check README.md for detailed usage instructions")
        print("• Review apps/core/db_router.py for multi-tenancy details")
        
        print("\n" + "=" * 60)
        print("Thank you for using Zain HMS!")
        print("=" * 60)


def main():
    """Main setup function"""
    setup = SaaSSetup()
    setup.run_setup()


if __name__ == "__main__":
    main()
