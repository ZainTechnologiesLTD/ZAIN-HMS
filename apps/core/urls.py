# apps/core/urls.py
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Dashboard
    path('', views.DashboardView.as_view(), name='dashboard'),
    
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
