# apps/core/api_urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

app_name = 'core_api'

router = DefaultRouter()
router.register(r'notifications', api_views.NotificationViewSet, basename='notifications')
router.register(r'activity-logs', api_views.ActivityLogViewSet, basename='activity-logs')

urlpatterns = [
    # Router URLs
    path('', include(router.urls)),
    
    # Dashboard API
    path('dashboard/stats/', api_views.DashboardStatsAPIView.as_view(), name='dashboard_stats'),
    
    # Search API
    path('search/', api_views.GlobalSearchAPIView.as_view(), name='global_search'),
    
    # System Configuration API
    path('config/', api_views.SystemConfigurationAPIView.as_view(), name='system_config'),
    
    # User Profile API
    path('profile/', api_views.UserProfileAPIView.as_view(), name='user_profile'),
    path('profile/update/', api_views.UpdateUserProfileAPIView.as_view(), name='update_profile'),
    
    # File Upload API
    path('upload/', api_views.FileUploadAPIView.as_view(), name='file_upload'),
    
    # Notification Actions API
    path('notifications/mark-read/', api_views.MarkNotificationsReadAPIView.as_view(), name='mark_notifications_read'),
    path('notifications/bulk-action/', api_views.BulkNotificationActionAPIView.as_view(), name='bulk_notification_action'),
    
    # Update System API endpoints
    path('system/check-updates/', api_views.CheckUpdatesView.as_view(), name='check-updates'),
    path('system/update/', api_views.UpdateSystemView.as_view(), name='system-update'),
    path('system/notifications/', api_views.UpdateNotificationsView.as_view(), name='update-notifications'),
    path('system/status/', api_views.SystemStatusView.as_view(), name='system-status'),
]
