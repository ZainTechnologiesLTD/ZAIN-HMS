# apps/tenants/management/commands/verify_hospital_modules.py
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connections
from apps.tenants.models import Tenant

class Command(BaseCommand):
    help = 'Verify that all necessary modules have been migrated to hospital databases'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hospital',
            type=str,
            help='Check specific hospital by subdomain (e.g., demo-hospital)'
        )
        parser.add_argument(
            '--detailed',
            action='store_true',
            help='Show detailed table information for each module'
        )

    def handle(self, *args, **options):
        hospital_subdomain = options.get('hospital')
        detailed = options.get('detailed', False)
        
        if hospital_subdomain:
            # Check specific hospital
            try:
                hospital = Tenant.objects.get(subdomain=hospital_subdomain)
                self.verify_hospital_database(hospital, detailed)
            except Tenant.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Hospital with subdomain "{hospital_subdomain}" not found')
                )
                return
        else:
            # Check all hospitals
            hospitals = Tenant.objects.all().order_by('name')
            if not hospitals.exists():
                self.stdout.write(
                    self.style.WARNING('No hospitals found in the system')
                )
                return
                
            for hospital in hospitals:
                self.verify_hospital_database(hospital, detailed)
                self.stdout.write('')  # Add spacing between hospitals

    def verify_hospital_database(self, hospital, detailed=False):
        """Verify database and modules for a specific hospital"""
        self.stdout.write(
            self.style.SUCCESS(f'🏥 {hospital.name} ({hospital.subdomain})')
        )
        self.stdout.write('=' * 60)
        
        db_name = f'hospital_{hospital.subdomain}'
        
        # Check if database is configured
        if db_name not in settings.DATABASES:
            self.stdout.write(
                self.style.ERROR(f'❌ Database {db_name} not configured in Django settings')
            )
            return
            
        try:
            connection = connections[db_name]
            with connection.cursor() as cursor:
                # Get all tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
                all_tables = [row[0] for row in cursor.fetchall()]
                
                self.stdout.write(f'📊 Total Tables: {len(all_tables)}')
                self.stdout.write('')
                
                # Define expected modules and their key tables
                expected_modules = {
                    'Core Django': {
                        'tables': ['auth_user', 'auth_group', 'auth_permission', 'django_content_type', 'django_migrations'],
                        'description': 'Authentication and core Django functionality'
                    },
                    'Patient Management': {
                        'tables': ['patients_patient', 'patients_patientdocument', 'patients_patientnote', 'patients_patientvitals'],
                        'description': 'Patient records, documents, notes, and vital signs'
                    },
                    'Appointments': {
                        'tables': ['appointments_appointment', 'appointments_appointmentslot'],
                        'description': 'Appointment scheduling and management'
                    },
                    'Doctor Management': {
                        'tables': ['doctors_doctor', 'doctors_doctorschedule', 'doctors_specialization'],
                        'description': 'Doctor profiles and schedules'
                    },
                    'Nurse Management': {
                        'tables': ['nurses_nurse', 'nurses_nurseschedule'],
                        'description': 'Nursing staff management'
                    },
                    'Staff Management': {
                        'tables': ['staff_staff', 'staff_department'],
                        'description': 'General staff and department management'
                    },
                    'Billing & Finance': {
                        'tables': ['billing_invoice', 'billing_payment', 'billing_insuranceclaim'],
                        'description': 'Billing, payments, and insurance management'
                    },
                    'Laboratory': {
                        'tables': ['laboratory_labtest', 'laboratory_testresult', 'laboratory_equipment'],
                        'description': 'Laboratory tests and equipment'
                    },
                    'Emergency Care': {
                        'tables': ['emergency_emergencyrecord', 'emergency_triage'],
                        'description': 'Emergency department management'
                    },
                    'Surgery Management': {
                        'tables': ['surgery_surgery', 'surgery_operatingroom'],
                        'description': 'Surgical procedures and operating rooms'
                    },
                    'Telemedicine': {
                        'tables': ['telemedicine_consultation', 'telemedicine_videosession'],
                        'description': 'Virtual consultations and telemedicine'
                    },
                    'Room Management': {
                        'tables': ['ipd_room', 'ipd_bed', 'ipd_ipdrecord'],
                        'description': 'Hospital rooms, beds, and IPD management'
                    },
                    'Notifications': {
                        'tables': ['notifications_notification'],
                        'description': 'System notifications and alerts'
                    },
                    'Contact Management': {
                        'tables': ['contact_contact', 'contact_message'],
                        'description': 'Contact information and messaging'
                    },
                    'Celery (Background Tasks)': {
                        'tables': ['django_celery_beat_periodictask', 'django_celery_results_taskresult'],
                        'description': 'Background task scheduling and results'
                    }
                }
                
                # Check each module
                total_modules = len(expected_modules)
                working_modules = 0
                
                for module_name, module_info in expected_modules.items():
                    module_tables = module_info['tables']
                    description = module_info['description']
                    
                    # Check which tables exist
                    existing_tables = [table for table in module_tables if table in all_tables]
                    missing_tables = [table for table in module_tables if table not in all_tables]
                    
                    if existing_tables:
                        working_modules += 1
                        status = f"✅ {len(existing_tables)}/{len(module_tables)} tables"
                        if missing_tables:
                            status = f"⚠️  {len(existing_tables)}/{len(module_tables)} tables"
                    else:
                        status = "❌ No tables found"
                    
                    self.stdout.write(f'{status} {module_name}')
                    
                    if detailed:
                        self.stdout.write(f'    📝 {description}')
                        if existing_tables:
                            self.stdout.write(f'    ✅ Found: {", ".join(existing_tables)}')
                        if missing_tables:
                            self.stdout.write(f'    ❌ Missing: {", ".join(missing_tables)}')
                        self.stdout.write('')
                
                # Summary
                self.stdout.write('')
                self.stdout.write(f'📈 Module Summary: {working_modules}/{total_modules} modules have tables')
                
                # Overall status
                if working_modules >= total_modules * 0.9:  # 90% or more modules working
                    overall_status = "🟢 Excellent - Hospital fully functional"
                elif working_modules >= total_modules * 0.7:  # 70% or more modules working
                    overall_status = "🟡 Good - Most modules working"
                else:
                    overall_status = "🔴 Needs attention - Many modules missing"
                
                self.stdout.write(f'🎯 Overall Status: {overall_status}')
                
                # Check for any unexpected tables (might indicate additional modules)
                expected_table_prefixes = [
                    'auth_', 'django_', 'patients_', 'appointments_', 'doctors_', 'nurses_',
                    'staff_', 'billing_', 'laboratory_', 'emergency_', 'surgery_',
                    'telemedicine_', 'ipd_', 'notifications_', 'contact_', 'celery_'
                ]
                
                unexpected_tables = []
                for table in all_tables:
                    if not any(table.startswith(prefix) for prefix in expected_table_prefixes):
                        unexpected_tables.append(table)
                
                if unexpected_tables:
                    self.stdout.write('')
                    self.stdout.write(f'🆕 Additional Tables Found: {len(unexpected_tables)}')
                    if detailed:
                        for table in unexpected_tables[:10]:  # Show first 10
                            self.stdout.write(f'    • {table}')
                        if len(unexpected_tables) > 10:
                            self.stdout.write(f'    ... and {len(unexpected_tables) - 10} more')
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error accessing database: {str(e)}')
            )
