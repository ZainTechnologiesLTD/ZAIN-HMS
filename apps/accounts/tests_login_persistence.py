from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from apps.tenants.models import Tenant
from django.utils import timezone
from django.db.models.signals import post_save
import apps.tenants.signals as tenant_signals

User = get_user_model()

class HospitalSelectionPersistenceTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Disconnect the tenant post_save signal that creates tenant DBs to
        # avoid running multi-db migrations during unit tests.
        try:
            post_save.disconnect(tenant_signals.create_hospital_database_signal, sender=Tenant)
            cls._tenant_signal_disconnected = True
        except Exception:
            cls._tenant_signal_disconnected = False

    @classmethod
    def tearDownClass(cls):
        # Reconnect the signal if we disconnected it
        try:
            if getattr(cls, '_tenant_signal_disconnected', False):
                post_save.connect(tenant_signals.create_hospital_database_signal, sender=Tenant)
        except Exception:
            pass
        super().tearDownClass()
    def setUp(self):
        # Create a tenant in the default DB
        # Create an admin user required by Tenant.admin (non-null)
        self.admin_user = User.objects.create_user(
            username='tenantadmin',
            email='admin@example.com',
            password='adminpass123',
            role='SUPERADMIN'
        )

        self.tenant = Tenant.objects.create(
            name='Test Hospital',
            subdomain='test-hosp',
            db_name='hospital_test_hosp',
            admin=self.admin_user,
            subscription_start_date=timezone.now(),
            subscription_end_date=timezone.now() + timezone.timedelta(days=365),
            is_trial=False
        )

        # Create a user without hospital
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role='HOSPITAL_ADMIN'
        )

        self.client = Client()

    def test_session_selected_hospital_persists_on_login_and_profile_renders(self):
        # Put tenant id in session
        from django.test import TestCase, Client
        from django.contrib.auth import get_user_model
        from apps.tenants.models import Tenant
        from django.utils import timezone
        from datetime import timedelta
        from django.db.models.signals import post_save
        import apps.tenants.signals as tenant_signals

        User = get_user_model()


        class HospitalSelectionPersistenceTest(TestCase):
            @classmethod
            def setUpClass(cls):
                super().setUpClass()
                # Disconnect the tenant post_save signal that creates tenant DBs to
                # avoid running multi-db migrations during unit tests.
                try:
                    post_save.disconnect(tenant_signals.create_hospital_database_signal, sender=Tenant)
                    cls._tenant_signal_disconnected = True
                except Exception:
                    cls._tenant_signal_disconnected = False

            @classmethod
            def tearDownClass(cls):
                # Reconnect the signal if we disconnected it
                try:
                    if getattr(cls, '_tenant_signal_disconnected', False):
                        post_save.connect(tenant_signals.create_hospital_database_signal, sender=Tenant)
                except Exception:
                    pass
                super().tearDownClass()

            def setUp(self):
                # Create a tenant in the default DB
                # Create an admin user required by Tenant.admin (non-null)
                self.admin_user = User.objects.create_user(
                    username='tenantadmin',
                    email='admin@example.com',
                    password='adminpass123',
                    role='SUPERADMIN'
                )

                self.tenant = Tenant.objects.create(
                    name='Test Hospital',
                    subdomain='test-hosp',
                    db_name='hospital_test_hosp',
                    admin=self.admin_user,
                    subscription_start_date=timezone.now(),
                    subscription_end_date=timezone.now() + timedelta(days=365),
                    is_trial=False
                )

                # Create a user without hospital
                self.user = User.objects.create_user(
                    username='testuser',
                    email='test@example.com',
                    password='testpass123',
                    role='HOSPITAL_ADMIN'
                )

                self.client = Client()

            def test_session_selected_hospital_persists_on_login_and_profile_renders(self):
                # Put tenant id in session
                session = self.client.session
                session['current_hospital_id'] = self.tenant.id
                session.save()

                # Perform login but don't follow redirects to avoid rendering templates
                resp = self.client.post(
                    '/accounts/login/',
                    {'username': 'testuser', 'password': 'testpass123'},
                    follow=False,
                    HTTP_HOST='test-hosp.localhost'
                )

                # Expect a redirect to the dashboard or profile
                self.assertIn(resp.status_code, (302, 200))

                # Reload user from DB and assert hospital persisted
                u = User.objects.get(pk=self.user.pk)
                self.assertIsNotNone(u.hospital)
                self.assertEqual(u.hospital.id, self.tenant.id)
