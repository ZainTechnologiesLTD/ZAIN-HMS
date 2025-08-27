#!/usr/bin/env python
"""
Initialize billing module with basic data
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zain_hms.settings')
django.setup()

from apps.billing.models import ServiceCategory, MedicalService
from decimal import Decimal

def initialize_billing_data():
    """Add basic billing data"""
    print("Initializing billing module with basic data...")
    
    # Create basic service categories
    categories_data = [
        {
            'name': 'Consultation',
            'description': 'Doctor consultation services'
        },
        {
            'name': 'Laboratory',
            'description': 'Laboratory tests and diagnostics'
        },
        {
            'name': 'Radiology',
            'description': 'Imaging and radiology services'
        },
        {
            'name': 'Surgery',
            'description': 'Surgical procedures'
        },
        {
            'name': 'Emergency',
            'description': 'Emergency department services'
        },
        {
            'name': 'Pharmacy',
            'description': 'Medication and pharmaceutical services'
        }
    ]
    
    categories_created = 0
    for cat_data in categories_data:
        category, created = ServiceCategory.objects.get_or_create(
            name=cat_data['name'],
            defaults={'description': cat_data['description']}
        )
        if created:
            categories_created += 1
            print(f"  ✓ Created category: {category.name}")
    
    print(f"Created {categories_created} new service categories")
    
    # Create basic medical services
    services_data = [
        {
            'category': 'Consultation',
            'code': 'CONS001',
            'name': 'General Consultation',
            'description': 'General doctor consultation',
            'base_price': Decimal('50.00'),
            'duration_minutes': 30
        },
        {
            'category': 'Consultation',
            'code': 'CONS002',
            'name': 'Specialist Consultation',
            'description': 'Specialist doctor consultation',
            'base_price': Decimal('100.00'),
            'duration_minutes': 45
        },
        {
            'category': 'Laboratory',
            'code': 'LAB001',
            'name': 'Complete Blood Count',
            'description': 'CBC blood test',
            'base_price': Decimal('25.00'),
            'duration_minutes': 15
        },
        {
            'category': 'Laboratory',
            'code': 'LAB002',
            'name': 'Blood Sugar Test',
            'description': 'Blood glucose level test',
            'base_price': Decimal('15.00'),
            'duration_minutes': 10
        },
        {
            'category': 'Radiology',
            'code': 'RAD001',
            'name': 'X-Ray Chest',
            'description': 'Chest X-ray examination',
            'base_price': Decimal('75.00'),
            'duration_minutes': 20
        },
        {
            'category': 'Emergency',
            'code': 'EMR001',
            'name': 'Emergency Room Visit',
            'description': 'Emergency department consultation',
            'base_price': Decimal('150.00'),
            'duration_minutes': 60
        }
    ]
    
    services_created = 0
    for service_data in services_data:
        category = ServiceCategory.objects.get(name=service_data['category'])
        service, created = MedicalService.objects.get_or_create(
            code=service_data['code'],
            defaults={
                'category': category,
                'name': service_data['name'],
                'description': service_data['description'],
                'base_price': service_data['base_price'],
                'duration_minutes': service_data['duration_minutes']
            }
        )
        if created:
            services_created += 1
            print(f"  ✓ Created service: {service.code} - {service.name}")
    
    print(f"Created {services_created} new medical services")
    print("\n✅ Billing module initialization complete!")
    print("The billing module is now ready to use with basic service categories and services.")

if __name__ == '__main__':
    initialize_billing_data()
