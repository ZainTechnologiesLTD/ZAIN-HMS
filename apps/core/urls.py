# apps/core/urls.py
from django.urls import path
from . import views
from .qr_views import QRScannerView, QRSearchView
from .barcode_views import BarcodeScannerView, barcode_search, manual_search, generate_barcode
from .admin_views import admin_logout_view

app_name = 'core'

urlpatterns = [
    # Admin Logout (for proper admin interface logout redirect)
    path('admin-logout/', admin_logout_view, name='admin_logout'),
    
    # Dashboard
    path('', views.DashboardView.as_view(), name='home'),
    
    # QR Code Scanner (legacy)
    path('qr-scanner/', QRScannerView.as_view(), name='qr_scanner'),
    path('qr-search/', QRSearchView.as_view(), name='qr_search'),
    
    # Barcode Scanner (new hospital standard)
    path('barcode-scanner/', BarcodeScannerView.as_view(), name='barcode_scanner'),
    path('barcode-search/', barcode_search, name='barcode_search'),
    path('generate-barcode/', generate_barcode, name='generate_barcode'),
    path('manual-search/', manual_search, name='manual_search'),
    
    # Notifications
    path('notifications/', views.NotificationListView.as_view(), name='notifications'),
    path('notifications/<uuid:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('api/notifications/', views.get_notifications, name='api_notifications'),
    
    # Activity Logs
    path('activity-logs/', views.ActivityLogView.as_view(), name='activity_logs'),
    
    # System Configuration
    path('settings/', views.SystemConfigurationView.as_view(), name='system_config'),
    
    # Profile
    path('profile/', views.ProfileView.as_view(), name='profile'),
    
    # Search and Export
    path('search/', views.search_global, name='global_search'),
    path('export/', views.export_data, name='export_data'),
]
