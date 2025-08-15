# zain_hms/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.core.views import home_redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_redirect, name='home'),
    path('auth/', include('apps.accounts.urls')),
    path('dashboard/', include('apps.core.urls')),
    path('patients/', include('apps.patients.urls')),
    path('appointments/', include('apps.appointments.urls')),
    path('doctors/', include('apps.doctors.urls')),
    path('nurses/', include('apps.nurses.urls')),
    path('billing/', include('apps.billing.urls')),
    path('pharmacy/', include('apps.pharmacy.urls')),
    path('laboratory/', include('apps.laboratory.urls')),
    path('emergency/', include('apps.emergency.urls')),
    path('reports/', include('apps.reports.urls')),
    path('api/', include('apps.core.api_urls')),
    # Optional modules (create URLs when ready)
    # path('inventory/', include('apps.inventory.urls')),
    # path('analytics/', include('apps.analytics.urls')),
    # path('hr/', include('apps.hr.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
