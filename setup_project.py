#!/usr/bin/env python
"""
ZAIN HMS - Project Setup Script
This script helps set up the project quickly for development.
"""

import os
import sys
import django
from django.core.management import execute_from_command_line
from django.contrib.auth import get_user_model

def setup_django():
    """Setup Django settings"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zain_hms.settings')
    django.setup()

def create_sample_data():
    """Create sample data for testing"""
    from apps.accounts.models import Hospital, Department, User
    from apps.core.models import SystemConfiguration
    
    print("Creating sample hospital...")
    
    # Create sample hospital
    hospital, created = Hospital.objects.get_or_create(
        code='ZAIN001',
        defaults={
            'name': 'ZAIN Medical Center',
            'address': '123 Healthcare Street, Medical District',
            'city': 'Healthcare City',
            'state': 'Medical State',
            'country': 'Healthcare Country',
            'postal_code': '12345',
            'phone': '+1234567890',
            'email': 'info@zainmedical.com',
            'subscription_plan': 'PROFESSIONAL',
            'subscription_status': 'ACTIVE'
        }
    )
    
    if created:
        print(f"✅ Created hospital: {hospital.name}")
    else:
        print(f"ℹ️ Hospital already exists: {hospital.name}")
    
    # Create system configuration
    config, created = SystemConfiguration.objects.get_or_create(
        hospital=hospital,
        defaults={
            'hospital_name': hospital.name,
            'contact_email': hospital.email,
            'contact_phone': hospital.phone,
            'address': hospital.address,
            'consultation_fee': 50.00,
            'currency_code': 'USD',
            'appointment_duration': 30,
            'patient_id_prefix': 'PAT',
            'auto_generate_patient_id': True,
        }
    )
    
    if created:
        print("✅ Created system configuration")
    
    # Create departments
    departments = [
        {'name': 'Cardiology', 'code': 'CARD'},
        {'name': 'Neurology', 'code': 'NEUR'},
        {'name': 'Orthopedics', 'code': 'ORTH'},
        {'name': 'Pediatrics', 'code': 'PEDI'},
        {'name': 'Emergency', 'code': 'EMER'},
        {'name': 'General Medicine', 'code': 'GENM'},
    ]
    
    for dept_data in departments:
        dept, created = Department.objects.get_or_create(
            hospital=hospital,
            code=dept_data['code'],
            defaults={
                'name': dept_data['name'],
                'description': f"{dept_data['name']} Department"
            }
        )
        if created:
            print(f"✅ Created department: {dept.name}")
    
    # Create sample users
    User = get_user_model()
    
    # Admin user
    if not User.objects.filter(username='admin').exists():
        admin = User.objects.create_user(
            username='admin',
            email='admin@zainmedical.com',
            password='admin123',
            first_name='System',
            last_name='Administrator',
            hospital=hospital,
            role='ADMIN',
            is_staff=True,
            is_superuser=True,
            is_approved=True
        )
        print(f"✅ Created admin user: {admin.username}")
    
    # Doctor user
    if not User.objects.filter(username='doctor1').exists():
        cardiology_dept = Department.objects.get(hospital=hospital, code='CARD')
        doctor = User.objects.create_user(
            username='doctor1',
            email='doctor1@zainmedical.com',
            password='doctor123',
            first_name='John',
            last_name='Smith',
            hospital=hospital,
            department=cardiology_dept,
            role='DOCTOR',
            specialization='Cardiology',
            license_number='MD001',
            is_approved=True
        )
        print(f"✅ Created doctor user: {doctor.username}")
    
    # Nurse user
    if not User.objects.filter(username='nurse1').exists():
        nurse = User.objects.create_user(
            username='nurse1',
            email='nurse1@zainmedical.com',
            password='nurse123',
            first_name='Jane',
            last_name='Johnson',
            hospital=hospital,
            role='NURSE',
            is_approved=True
        )
        print(f"✅ Created nurse user: {nurse.username}")
    
    # Receptionist user
    if not User.objects.filter(username='reception1').exists():
        reception = User.objects.create_user(
            username='reception1',
            email='reception@zainmedical.com',
            password='reception123',
            first_name='Mary',
            last_name='Wilson',
            hospital=hospital,
            role='RECEPTIONIST',
            is_approved=True
        )
        print(f"✅ Created receptionist user: {reception.username}")

def main():
    """Main setup function"""
    print("🏥 ZAIN HMS - Project Setup")
    print("=" * 50)
    
    try:
        # Setup Django
        setup_django()
        
        # Run migrations
        print("\n📦 Running database migrations...")
        execute_from_command_line(['manage.py', 'makemigrations'])
        execute_from_command_line(['manage.py', 'migrate'])
        
        # Create sample data
        print("\n🎭 Creating sample data...")
        create_sample_data()
        
        print("\n" + "=" * 50)
        print("✅ Setup completed successfully!")
        print("\n📋 Login Credentials:")
        print("Admin: admin / admin123")
        print("Doctor: doctor1 / doctor123")
        print("Nurse: nurse1 / nurse123")
        print("Reception: reception1 / reception123")
        print("\n🚀 Run: python manage.py runserver")
        print("🌐 Visit: http://127.0.0.1:8000")
        
    except Exception as e:
        print(f"\n❌ Error during setup: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
