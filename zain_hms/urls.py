# zain_hms/urls.py - Main project URLs
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.i18n import set_language
from apps.core.admin_views import admin_logout_view
from . import views

urlpatterns = [
    # Custom admin logout that stays in admin context (must be before admin/ to override)
    path('admin/logout/', admin_logout_view, name='admin_logout'),
    # Django admin
    path('admin/', admin.site.urls),
    
    # Public landing page (root URL)
    path('', views.home, name='home'),
    
    # Dashboard functionality 
    path('dashboard/', include('apps.dashboard.urls', namespace='dashboard')),
    
    # Core functionality (barcode scanner, QR scanner, etc.)
    path('core/', include('apps.core.urls', namespace='core')),
    
    # Essential Apps  
    path('patients/', include('apps.patients.urls', namespace='patients')),
    path('doctors/', include('apps.doctors.urls', namespace='doctors')),
    path('appointments/', include('apps.appointments.urls', namespace='appointments')),
    path('billing/', include('apps.billing.urls', namespace='billing')),
    path('pharmacy/', include('apps.pharmacy.urls', namespace='pharmacy')),
    path('laboratory/', include('apps.laboratory.urls', namespace='laboratory')),
    path('radiology/', include('apps.radiology.urls', namespace='radiology')),
    path('emergency/', include('apps.emergency.urls', namespace='emergency')),
    path('nurses/', include('apps.nurses.urls', namespace='nurses')),
    path('reports/', include('apps.reports.urls', namespace='reports')),
    path('telemedicine/', include('apps.telemedicine.urls', namespace='telemedicine')),
    
    # Additional Apps (verified working)
    path('ipd/', include('apps.ipd.urls', namespace='ipd')),
    path('tenants/', include('apps.tenants.urls', namespace='tenants')),
    
    # Additional Apps (verified working)
    path('staff/', include('apps.staff.urls', namespace='staff')),
    # path('surgery/', include('apps.surgery.urls', namespace='surgery')),
    # path('inventory/', include('apps.inventory.urls', namespace='inventory')),
    # path('analytics/', include('apps.analytics.urls', namespace='analytics')),
    path('notifications/', include('apps.notifications.urls', namespace='notifications')),
    
    # Authentication & User Management
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/', include('apps.accounts.urls', namespace='accounts')),
    
    # Language switching
    path('set_language/', set_language, name='set_language'),
    
    # API endpoints
    path('api/medicines/', views.medicine_search_api, name='medicine_search_api'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
