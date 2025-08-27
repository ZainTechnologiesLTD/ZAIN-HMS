# apps/tenants/management/commands/create_test_hospital.py
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from apps.tenants.models import Tenant, TenantAccess
from apps.core.db_router import TenantDatabaseManager

User = get_user_model()

class Command(BaseCommand):
    help = 'Create a test hospital with database setup for testing the automatic migration feature'

    def add_arguments(self, parser):
        parser.add_argument(
            '--name',
            type=str,
            default='Test Hospital',
            help='Hospital name'
        )
        parser.add_argument(
            '--subdomain',
            type=str,
            default='test-hospital',
            help='Hospital subdomain (will be used as database identifier)'
        )
        parser.add_argument(
            '--admin-username',
            type=str,
            default='hospital_admin',
            help='Username for hospital administrator'
        )
        parser.add_argument(
            '--admin-email',
            type=str,
            default='admin@testhospital.com',
            help='Email for hospital administrator'
        )
        parser.add_argument(
            '--admin-password',
            type=str,
            default='testpassword123',
            help='Password for hospital administrator'
        )
        parser.add_argument(
            '--skip-database',
            action='store_true',
            help='Skip automatic database creation (for testing admin interface)'
        )

    def handle(self, *args, **options):
        hospital_name = options['name']
        subdomain = options['subdomain']
        admin_username = options['admin_username']
        admin_email = options['admin_email']
        admin_password = options['admin_password']
        skip_database = options['skip_database']
        
        self.stdout.write(
            self.style.SUCCESS(f'🏥 Creating test hospital: {hospital_name}')
        )
        
        try:
            # Check if hospital already exists
            if Tenant.objects.filter(subdomain=subdomain).exists():
                raise CommandError(f'Hospital with subdomain "{subdomain}" already exists')
            
            # Create admin user
            admin_user, created = User.objects.get_or_create(
                username=admin_username,
                defaults={
                    'email': admin_email,
                    'first_name': 'Hospital',
                    'last_name': 'Administrator',
                    'role': 'HOSPITAL_ADMIN',
                    'is_active': True,
                    'is_staff': False,
                    'is_superuser': False
                }
            )
            
            if created:
                admin_user.set_password(admin_password)
                admin_user.save()
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Created admin user: {admin_username}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'⚠️  Admin user already exists: {admin_username}')
                )
            
            # Create hospital
            hospital = Tenant.objects.create(
                name=hospital_name,
                subdomain=subdomain,
                db_name=f'hospital_{subdomain}',
                admin=admin_user,
                address='123 Test Hospital Street, Test City, TC 12345',
                phone='+1-555-TEST-HOSPITAL',
                email=admin_email,
                subscription_plan='BASIC',
                subscription_start_date=timezone.now(),
                subscription_end_date=timezone.now() + timedelta(days=30),
                is_trial=True,
                is_active=True,
                telemedicine_enabled=True,
                laboratory_enabled=True,
                radiology_enabled=True,
                pharmacy_enabled=True,
                billing_enabled=True,
                ipd_enabled=True,
                emergency_enabled=True
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ Created hospital: {hospital_name}')
            )
            
            # Create TenantAccess
            TenantAccess.objects.create(
                user=admin_user,
                tenant=hospital,
                role='HOSPITAL_ADMIN',
                is_active=True
            )
            
            self.stdout.write(
                self.style.SUCCESS('✅ Created hospital access permissions')
            )
            
            # Create database (unless skipped)
            if not skip_database:
                self.stdout.write(
                    self.style.WARNING('🔄 Creating hospital database with all modules...')
                )
                
                try:
                    TenantDatabaseManager.create_hospital_database(subdomain)
                    self.stdout.write(
                        self.style.SUCCESS('✅ Hospital database created successfully!')
                    )
                    
                    # List the modules that were migrated
                    modules = [
                        'Patient Management', 'Appointments', 'Doctors & Staff',
                        'Nurses', 'Billing', 'Laboratory', 'Emergency',
                        'Inventory', 'Analytics', 'Surgery', 'Telemedicine',
                        'Room Management', 'OPD/IPD', 'Notifications'
                    ]
                    
                    self.stdout.write('')
                    self.stdout.write(self.style.SUCCESS('📋 Migrated Modules:'))
                    for module in modules:
                        self.stdout.write(f'   ✅ {module}')
                        
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'❌ Database creation failed: {str(e)}')
                    )
                    self.stdout.write(
                        self.style.WARNING(
                            '💡 You can create the database manually using the admin interface'
                        )
                    )
            else:
                self.stdout.write(
                    self.style.WARNING('⏭️  Skipped database creation (use --skip-database=false to create)')
                )
            
            # Display access information
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('🎉 Test Hospital Created Successfully!'))
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('📋 Access Information:'))
            self.stdout.write(f'   Hospital Name: {hospital_name}')
            self.stdout.write(f'   Subdomain: {subdomain}')
            self.stdout.write(f'   Database: hospital_{subdomain}')
            self.stdout.write(f'   Admin Username: {admin_username}')
            self.stdout.write(f'   Admin Password: {admin_password}')
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('🔗 Access URLs:'))
            
            from apps.tenants.utils import AllowedHostsManager
            hospital_url = AllowedHostsManager.get_hospital_url(subdomain)
            self.stdout.write(f'   Hospital Dashboard: {hospital_url}')
            self.stdout.write(f'   Django Admin: http://127.0.0.1:8000/admin/')
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('🌐 Domain Configuration:'))
            self.stdout.write(f'   Domain: {subdomain}.localhost (automatically added to ALLOWED_HOSTS)')
            self.stdout.write('')
            self.stdout.write(
                self.style.WARNING(
                    '💡 Now you can test creating more hospitals through the Django admin interface!'
                )
            )
            
        except Exception as e:
            raise CommandError(f'Failed to create test hospital: {str(e)}')
