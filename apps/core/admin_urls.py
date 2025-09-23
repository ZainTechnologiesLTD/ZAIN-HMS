# apps/core/admin_urls.py
from django.urls import path
from .admin_views import module_management, toggle_hospital_module

app_name = 'admin'

urlpatterns = [
    # Module Management (accessed as /admin/modules/)
    path('', module_management, name='module_management'),
    path('toggle/<uuid:hospital_id>/<str:module_type>/', toggle_hospital_module, name='toggle_hospital_module'),
]
