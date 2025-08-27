from django.test import SimpleTestCase, RequestFactory
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

from apps.dashboard import views as dashboard_views


class DashboardViewUnitTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def _make_request(self):
        request = self.factory.get('/dashboard/')
        # attach a simple session
        from django.contrib.sessions.middleware import SessionMiddleware
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session['selected_hospital_id'] = 1
        # fake authenticated user
        request.user = SimpleNamespace(role='HOSPITAL_ADMIN', is_authenticated=True)
        return request

    def test_dashboard_renders_with_mocked_models(self):
        req = self._make_request()

        # Patch models and render to avoid DB and template rendering
        with patch('apps.dashboard.views.Patient') as mock_patient, \
             patch('apps.dashboard.views.Bill') as mock_bill, \
             patch('apps.dashboard.views.Appointment') as mock_appt, \
             patch('apps.dashboard.views.render') as mock_render:

            # Configure mocks
            mock_hosp = MagicMock()
            mock_hosp.get_enabled_modules.return_value = []
            setattr(dashboard_views, 'Hospital', MagicMock(objects=MagicMock(get=MagicMock(return_value=mock_hosp))))

            mock_patient.objects.filter.return_value.count.return_value = 10

            mock_bill_qs = MagicMock()
            mock_bill_qs.count.return_value = 2
            mock_bill_qs.aggregate.return_value = {'total': 123.45}
            mock_bill_qs.order_by.return_value = [MagicMock(patient=SimpleNamespace(get_full_name=lambda: 'TP'), id='1', total_amount=100.0)]
            mock_bill.objects.filter.return_value = mock_bill_qs

            mock_appt_qs = MagicMock()
            mock_appt_qs.count.return_value = 5
            mock_appt_qs.order_by.return_value = [MagicMock(patient=SimpleNamespace(get_full_name=lambda: 'AP'), id='a')]
            mock_appt.objects.filter.return_value = mock_appt_qs

            # Make render return a simple HttpResponse-like object
            from django.http import HttpResponse
            mock_render.return_value = HttpResponse('ok')

            response = dashboard_views.dashboard_home(req)

            # view should have returned the mocked HttpResponse
            self.assertEqual(response.status_code, 200)
