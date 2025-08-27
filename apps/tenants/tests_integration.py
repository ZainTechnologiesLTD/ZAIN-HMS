from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from apps.tenants.models import Tenant, TenantAccess
from apps.patients.models import Patient
from apps.core.db_router import TenantDatabaseManager

User = get_user_model()

class TenantIntegrationTests(TestCase):
    databases = '__all__'

    def setUp(self):
        # Ensure hospital DBs are discovered and loaded
        TenantDatabaseManager.discover_and_load_hospital_databases()

        # Use an existing tenant if available
        self.tenant = Tenant.objects.using('default').filter(subdomain='ssd').first()
        if not self.tenant:
            # If not present, create a tenant record in default for test purposes
            self.tenant = Tenant.objects.using('default').create(
                name='ssd', subdomain='ssd', db_name='hospital_ssd'
            )

        # Ensure an admin user exists and is linked to the tenant
        self.admin = User.objects.using('default').filter(role='HOSPITAL_ADMIN').first()
        if not self.admin:
            # Create a simple admin user
            self.admin = User.objects.using('default').create_user(username='test_admin', password='pass', role='HOSPITAL_ADMIN')
        # Link admin to tenant
        self.admin.hospital_id = self.tenant.id
        self.admin.save(using='default')

    def test_tenant_and_access_in_default(self):
        # Tenant exists in default DB
        t = Tenant.objects.using('default').filter(subdomain='ssd').first()
        self.assertIsNotNone(t)
        # TenantAccess can be created in default DB
        ta, created = TenantAccess.objects.using('default').update_or_create(user=self.admin, tenant=t, defaults={'role':'HOSPITAL_ADMIN','is_active':True})
        self.assertTrue(ta.pk is not None)

    def test_create_patient_in_tenant_db_via_orm(self):
        db_alias = TenantDatabaseManager.get_hospital_db_name('ssd')
        # Create a patient via ORM saving to tenant DB alias
        p = Patient(
            hospital=self.tenant,
            first_name='ORM',
            middle_name='',
            last_name='Patient',
            date_of_birth='1990-01-01',
            gender='M',
            phone='+10000000000',
            address_line1='1 Test St',
            city='City',
            state='State',
            postal_code='00000',
            emergency_contact_name='EC',
            emergency_contact_relationship='Friend',
            emergency_contact_phone='+10000000001',
            registered_by=self.admin
        )
        p.save(using=db_alias)
        cnt = Patient.objects.using(db_alias).count()
        self.assertGreaterEqual(cnt, 1)

    def test_create_patient_via_view(self):
        # Use test client to simulate web UI create
        c = Client()
        c.login(username=self.admin.username, password='pass')
        # Set session hospital code
        session = c.session
        session['selected_hospital_code'] = 'ssd'
        session.save()

        post_data = {
            'first_name':'Web',
            'middle_name':'',
            'last_name':'Tester',
            'date_of_birth':'2002-02-02',
            'gender':'F',
            'phone':'+10000000002',
            'address_line1':'2 Web St',
            'city':'WebCity',
            'state':'WebState',
            'postal_code':'00002',
            'emergency_contact_name':'EC',
            'emergency_contact_relationship':'Friend',
            'emergency_contact_phone':'+10000000003'
        }
        resp = c.post('/patients/create/', post_data, follow=True, HTTP_HOST='ssd.localhost')
        self.assertIn(resp.status_code, (200, 302))
        db_alias = TenantDatabaseManager.get_hospital_db_name('ssd')
        self.assertGreaterEqual(Patient.objects.using(db_alias).count(), 1)
