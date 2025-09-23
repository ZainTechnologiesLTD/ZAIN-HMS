"""
Dashboard URLs for ZAIN HMS
Modern URL patterns with proper namespacing and API versioning.
"""
from django.urls import path, include
from . import views

# Import core functionality for integrated dashboard tools
try:
    from apps.core.barcode_views import BarcodeScannerView, barcode_search, manual_search, generate_barcode
    from apps.core.qr_views import QRScannerView, QRSearchView
    from apps.core.admin_views import admin_logout_view
    from apps.core.two_factor import setup_2fa, verify_2fa_setup, disable_2fa, regenerate_backup_codes
    CORE_IMPORTS_AVAILABLE = True
except ImportError:
    # Graceful degradation if core apps are not available
    CORE_IMPORTS_AVAILABLE = False

app_name = 'dashboard'

# Main Dashboard URLs
dashboard_patterns = [
    path('', views.DashboardHomeView.as_view(), name='home'),
    path('dashboard/', views.DashboardHomeView.as_view(), name='dashboard'),
    path('settings/', views.DashboardSettingsView.as_view(), name='settings'),
    path('analytics/', views.DashboardAnalyticsView.as_view(), name='analytics'),
    path('activity-log/', views.DashboardActivityView.as_view(), name='activity_log'),
]

# API URLs for dynamic content
api_patterns = [
    path('stats/', views.DashboardStatsAPIView.as_view(), name='api_stats'),
    path('activities/', views.DashboardActivitiesAPIView.as_view(), name='api_activities'),
    path('tasks/', views.DashboardTasksAPIView.as_view(), name='api_tasks'),
    path('charts/', views.DashboardChartsAPIView.as_view(), name='api_charts'),
    path('notifications/', views.DashboardNotificationsAPIView.as_view(), name='api_notifications'),
    path('layout/', views.DashboardLayoutAPIView.as_view(), name='api_layout'),
]

# HTMX endpoints for real-time updates
htmx_patterns = [
    path('stats/', views.htmx_dashboard_stats, name='htmx_stats'),
    path('activities/', views.htmx_recent_activities, name='htmx_activities'),
    path('tasks/', views.htmx_pending_tasks, name='htmx_tasks'),
    path('charts/', views.htmx_chart_data, name='htmx_charts'),
]

# Tools and utilities
tools_patterns = [
    # Search and Export
    path('search/', views.DashboardSearchView.as_view(), name='global_search'),
    path('export/', views.DashboardExportView.as_view(), name='export_data'),
    
    # Profile management
    path('profile/', views.DashboardProfileView.as_view(), name='profile'),
    
    # Notification management  
    path('notifications/mark-read/<int:notification_id>/', views.MarkNotificationReadView.as_view(), name='mark_notification_read'),
    path('notifications/settings/', views.NotificationSettingsView.as_view(), name='notification_settings'),
]

# Core integrated tools (if available)
if CORE_IMPORTS_AVAILABLE:
    core_tools_patterns = [
        # Barcode Scanner functionality
        path('barcode-scanner/', BarcodeScannerView.as_view(), name='barcode_scanner'),
        path('barcode-search/', barcode_search, name='barcode_search'),
        path('generate-barcode/', generate_barcode, name='generate_barcode'),
        path('manual-search/', manual_search, name='manual_search'),
        
        # QR Code Scanner functionality
        path('qr-scanner/', QRScannerView.as_view(), name='qr_scanner'),
        path('qr-search/', QRSearchView.as_view(), name='qr_search'),
        
        # Two-Factor Authentication
        path('setup-2fa/', setup_2fa, name='setup_2fa'),
        path('verify-2fa/', verify_2fa_setup, name='verify_2fa_setup'),
        path('disable-2fa/', disable_2fa, name='disable_2fa'),
        path('regenerate-backup-codes/', regenerate_backup_codes, name='regenerate_backup_codes'),
        
        # Admin utilities
        path('admin-logout/', admin_logout_view, name='admin_logout'),
    ]
else:
    core_tools_patterns = []

# Admin patterns
admin_patterns = [
    path('system/maintenance/', views.SystemMaintenanceView.as_view(), name='system_maintenance'),
    path('system/backup/', views.SystemBackupView.as_view(), name='system_backup'),
]

# Combine all URL patterns
urlpatterns = [
    # Dashboard main routes
    *dashboard_patterns,
    
    # Core integrated tools (direct access for backward compatibility)
    *core_tools_patterns,
    
    # API routes (versioned for future expansion)
    path('api/', include((api_patterns, 'api'), namespace='api')),
    
    # HTMX endpoints (both namespaced and direct access)
    path('htmx/', include((htmx_patterns, 'htmx'), namespace='htmx')),
    
    # Direct HTMX endpoints for template compatibility
    path('htmx/stats/', views.htmx_dashboard_stats, name='htmx_stats'),
    path('htmx/activities/', views.htmx_recent_activities, name='htmx_activities'),
    path('htmx/tasks/', views.htmx_pending_tasks, name='htmx_tasks'),
    path('htmx/charts/', views.htmx_chart_data, name='htmx_charts'),
    
    # Direct API endpoints for template compatibility
    path('api/stats/', views.DashboardStatsAPIView.as_view(), name='api_stats'),
    path('api/activities/', views.DashboardActivitiesAPIView.as_view(), name='api_activities'),
    path('api/tasks/', views.DashboardTasksAPIView.as_view(), name='api_tasks'),
    path('api/charts/', views.DashboardChartsAPIView.as_view(), name='api_charts'),
    path('api/notifications/', views.DashboardNotificationsAPIView.as_view(), name='api_notifications'),
    
    # Tools and utilities
    path('tools/', include((tools_patterns, 'tools'), namespace='tools')),
    
    # Profile and system configuration patterns  
    path('profile/', views.DashboardProfileView.as_view(), name='profile'),
    path('system-config/', views.SystemConfigView.as_view(), name='system_config'),
    path('notifications/mark-all-read/', views.MarkAllNotificationsReadView.as_view(), name='mark_all_notifications_read'),
    
    # Additional endpoints
    path('activity-log/', views.DashboardActivityView.as_view(), name='activity_log'),
    path('settings/', views.DashboardSettingsView.as_view(), name='settings'),
    
    # Admin patterns
    path('admin/', include((admin_patterns, 'admin'), namespace='admin')),
]