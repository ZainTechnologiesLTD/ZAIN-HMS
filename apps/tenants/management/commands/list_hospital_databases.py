# apps/tenants/management/commands/list_hospital_databases.py
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connections
from apps.tenants.models import Tenant

class Command(BaseCommand):
    help = 'List all hospital databases and their status'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🏥 Hospital Database Status Report')
        )
        self.stdout.write('=' * 60)
        
        hospitals = Tenant.objects.all().order_by('name')
        
        if not hospitals.exists():
            self.stdout.write(
                self.style.WARNING('No hospitals found in the system')
            )
            return
        
        for hospital in hospitals:
            self.stdout.write(f'\n🏥 {hospital.name}')
            self.stdout.write(f'   Subdomain: {hospital.subdomain}')
            
            db_name = f'hospital_{hospital.subdomain}'
            
            # Check if database is configured in settings
            if db_name in settings.DATABASES:
                self.stdout.write(f'   Database: ✅ {db_name} (configured)')
                
                # Try to connect and get table count
                try:
                    connection = connections[db_name]
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                        tables = cursor.fetchall()
                        table_count = len(tables)
                    
                    self.stdout.write(f'   Tables: ✅ {table_count} tables found')
                    
                    if table_count > 0:
                        # Show some key tables
                        key_tables = [
                            table[0] for table in tables 
                            if any(keyword in table[0] for keyword in [
                                'patient', 'appointment', 'doctor', 'nurse', 'billing'
                            ])
                        ]
                        if key_tables:
                            self.stdout.write(f'   Key Tables: {", ".join(key_tables[:5])}{"..." if len(key_tables) > 5 else ""}')
                    
                    # Check if hospital can accept data
                    status = "🟢 Ready" if table_count > 10 else "🟡 Incomplete" if table_count > 0 else "🔴 Empty"
                    self.stdout.write(f'   Status: {status}')
                    
                except Exception as e:
                    self.stdout.write(f'   Connection: ❌ Failed ({str(e)})')
                    self.stdout.write(f'   Status: 🔴 Error')
                    
            else:
                self.stdout.write(f'   Database: ❌ {db_name} (not configured)')
                self.stdout.write(f'   Status: 🔴 Missing')
            
            # Access URL
            self.stdout.write(f'   URL: http://{hospital.subdomain}.localhost:8000/')
            
            # Admin info
            if hospital.admin:
                self.stdout.write(f'   Admin: {hospital.admin.username} ({hospital.admin.get_full_name()})')
        
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(
            self.style.SUCCESS(f'✅ Listed {hospitals.count()} hospital(s)')
        )
        
        # Summary statistics
        configured_count = sum(1 for h in hospitals if f'hospital_{h.subdomain}' in settings.DATABASES)
        self.stdout.write(f'📊 {configured_count}/{hospitals.count()} hospitals have configured databases')
        
        # Instructions
        self.stdout.write('\n💡 To create missing databases:')
        self.stdout.write('   1. Use Django Admin: /admin/tenants/tenant/ → Select hospitals → "Create database"')
        self.stdout.write('   2. Use management command: python manage.py create_test_hospital')
        self.stdout.write('   3. Create manually: from apps.core.db_router import TenantDatabaseManager; TenantDatabaseManager.create_hospital_database("subdomain")')
