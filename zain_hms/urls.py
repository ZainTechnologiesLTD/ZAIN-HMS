# zain_hms/urls.py - Main project URLs
from django.contrib import admin
from django.urls import path, include
from apps.core import api as core_api
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.views.i18n import set_language
from apps.core.admin_views import admin_logout_view
from apps.core.admin_dashboard import admin_dashboard_data
from . import views

# Import the enhanced admin site

# Language-independent URLs (API, media, language switching)
urlpatterns = [
    # Root URL redirect to default language
    path('', views.language_root_redirect, name='language_root_redirect'),
    
    # Redirect old admin URLs to language-prefixed versions
    path('admin/', views.admin_language_redirect, name='admin_language_redirect'),
    path('admin/login/', views.admin_language_redirect, name='admin_login_redirect'),
    
    # Language switching endpoint (must be language-independent)
    path('set_language/', set_language, name='set_language'),
    
    # API endpoints (no language prefix needed)
    path('api/medicines/', views.medicine_search_api, name='medicine_search_api'),
    path('api/dashboard/metrics/', core_api.dashboard_metrics_api, name='dashboard_metrics_api'),
    path('api/user/preferences/', core_api.save_user_preferences, name='save_user_preferences'),
]

# Language-dependent URLs (all user-facing content including admin)
urlpatterns += i18n_patterns(
    # Public landing page (root URL with language)
    path('', views.home, name='home'),
    
    # Django admin (now with language prefix)
    path('admin/logout/', admin_logout_view, name='admin_logout'),
    path('admin/dashboard-data/', admin_dashboard_data, name='admin_dashboard_data'),
    path('admin/', admin.site.urls),
    
    # Dashboard functionality (consolidated - includes barcode scanner, notifications, etc.)
    path('dashboard/', include('apps.dashboard.urls', namespace='dashboard')),
    
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
    path('opd/', include('apps.opd.urls', namespace='opd')),
    
    # Additional Apps (verified working)
    path('staff/', include('apps.staff.urls', namespace='staff')),
    path('surgery/', include('apps.surgery.urls', namespace='surgery')),
    path('inventory/', include('apps.inventory.urls', namespace='inventory')),
    path('hr/', include('apps.hr.urls', namespace='hr')),
    path('analytics/', include('apps.analytics.urls', namespace='analytics')),
    path('emr/', include('apps.emr.urls', namespace='emr')),
    path('notifications/', include('apps.notifications.urls', namespace='notifications')),
    path('communications/', include('apps.communications.urls', namespace='communications')),
    
    # Authentication & User Management
    path('accounts/', include('apps.accounts.urls', namespace='accounts')),
    path('accounts/', include('django.contrib.auth.urls')),
    
    # Enable language prefix even for default language
    prefix_default_language=True
)

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
