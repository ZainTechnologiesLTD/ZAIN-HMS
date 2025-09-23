"""
Dashboard models for ZAIN HMS
Enterprise-grade models for dashboard analytics, widgets, and user preferences.
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.cache import cache
from django.db.models import Q, Count, Sum
import json
from datetime import datetime, timedelta

User = get_user_model()


class DashboardWidget(models.Model):
    """Configurable dashboard widgets for different user roles"""
    
    WIDGET_TYPES = [
        ('kpi_card', 'KPI Card'),
        ('chart', 'Chart'),
        ('table', 'Data Table'),
        ('activity_feed', 'Activity Feed'),
        ('quick_actions', 'Quick Actions'),
        ('calendar', 'Calendar'),
        ('notifications', 'Notifications'),
        ('tasks', 'Task List'),
    ]
    
    CHART_TYPES = [
        ('line', 'Line Chart'),
        ('bar', 'Bar Chart'),
        ('doughnut', 'Doughnut Chart'),
        ('pie', 'Pie Chart'),
        ('area', 'Area Chart'),
    ]
    
    name = models.CharField(max_length=100)
    widget_type = models.CharField(max_length=20, choices=WIDGET_TYPES)
    chart_type = models.CharField(max_length=20, choices=CHART_TYPES, null=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    query_config = models.JSONField(default=dict, help_text="Configuration for data queries")
    display_config = models.JSONField(default=dict, help_text="Display settings and styling")
    refresh_interval = models.PositiveIntegerField(default=30, help_text="Refresh interval in seconds")
    roles = models.JSONField(default=list, help_text="User roles that can see this widget")
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.title

    def is_accessible_by_role(self, user_role):
        """Check if widget is accessible by user role"""
        return not self.roles or user_role in self.roles


class UserDashboardLayout(models.Model):
    """User-specific dashboard layout and preferences"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='dashboard_layout')
    layout_config = models.JSONField(default=dict, help_text="Grid layout configuration")
    widget_settings = models.JSONField(default=dict, help_text="Per-widget user preferences")
    theme = models.CharField(max_length=20, default='light', choices=[
        ('light', 'Light'),
        ('dark', 'Dark'),
        ('auto', 'Auto'),
    ])
    sidebar_collapsed = models.BooleanField(default=False)
    notifications_enabled = models.BooleanField(default=True)
    auto_refresh_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Dashboard layout for {self.user.get_full_name()}"


class DashboardMetric(models.Model):
    """Store and track dashboard metrics for performance optimization"""
    
    metric_name = models.CharField(max_length=100, db_index=True)
    metric_value = models.JSONField()
    date = models.DateField(default=timezone.now)
    hour = models.PositiveIntegerField(null=True, blank=True)  # For hourly metrics
    calculated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['metric_name', 'date', 'hour']
        indexes = [
            models.Index(fields=['metric_name', 'date']),
            models.Index(fields=['date']),
        ]

    def __str__(self):
        return f"{self.metric_name} - {self.date}"

    @classmethod
    def get_cached_metric(cls, metric_name, date=None, hours_back=0):
        """Get cached metric with fallback to database"""
        if date is None:
            date = timezone.now().date()
        
        cache_key = f"dashboard_metric:{metric_name}:{date}:{hours_back}"
        cached_value = cache.get(cache_key)
        
        if cached_value is not None:
            return cached_value
        
        try:
            if hours_back > 0:
                hour = timezone.now().hour - hours_back
                metric = cls.objects.get(metric_name=metric_name, date=date, hour=hour)
            else:
                metric = cls.objects.get(metric_name=metric_name, date=date, hour=None)
            
            cache.set(cache_key, metric.metric_value, 300)  # Cache for 5 minutes
            return metric.metric_value
        except cls.DoesNotExist:
            return None


class ActivityLog(models.Model):
    """Enhanced activity logging for dashboard display"""
    
    ACTIVITY_TYPES = [
        ('user_action', 'User Action'),
        ('system_event', 'System Event'),
        ('data_change', 'Data Change'),
        ('security_event', 'Security Event'),
        ('integration', 'External Integration'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES, default='user_action')
    action = models.CharField(max_length=100)
    description = models.TextField()
    object_type = models.CharField(max_length=50, null=True, blank=True)
    object_id = models.CharField(max_length=50, null=True, blank=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='normal')
    metadata = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['activity_type', 'timestamp']),
        ]

    def __str__(self):
        user_name = self.user.get_full_name() if self.user else "System"
        return f"{user_name} - {self.action}"

    @classmethod
    def log_activity(cls, user, action, description, activity_type='user_action', 
                    object_type=None, object_id=None, priority='normal', 
                    metadata=None, request=None):
        """Create an activity log entry"""
        data = {
            'user': user,
            'action': action,
            'description': description,
            'activity_type': activity_type,
            'object_type': object_type,
            'object_id': str(object_id) if object_id else None,
            'priority': priority,
            'metadata': metadata or {},
        }
        
        if request:
            data['ip_address'] = cls._get_client_ip(request)
            data['user_agent'] = request.META.get('HTTP_USER_AGENT', '')[:500]
        
        return cls.objects.create(**data)

    @staticmethod
    def _get_client_ip(request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class DashboardAlert(models.Model):
    """System alerts and notifications for dashboard"""
    
    ALERT_TYPES = [
        ('info', 'Information'),
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ]
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES, default='info')
    target_roles = models.JSONField(default=list, help_text="Target user roles")
    target_users = models.ManyToManyField(User, blank=True, help_text="Specific target users")
    is_dismissible = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    auto_dismiss_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_alerts')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def is_visible_to_user(self, user):
        """Check if alert is visible to specific user"""
        if not self.is_active:
            return False
        
        if self.auto_dismiss_at and timezone.now() > self.auto_dismiss_at:
            return False
        
        # Check if user is specifically targeted
        if self.target_users.filter(id=user.id).exists():
            return True
        
        # Check if user's role is targeted
        if self.target_roles and user.role in self.target_roles:
            return True
        
        # If no specific targeting, show to all
        if not self.target_roles and not self.target_users.exists():
            return True
        
        return False


class DashboardCache(models.Model):
    """Dashboard-specific caching for complex queries"""
    
    cache_key = models.CharField(max_length=255, unique=True)
    cache_data = models.JSONField()
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['cache_key']),
            models.Index(fields=['expires_at']),
        ]

    @classmethod
    def get_or_set(cls, key, data_func, timeout=300):
        """Get cached data or set it if not exists/expired"""
        try:
            cache_obj = cls.objects.get(
                cache_key=key,
                expires_at__gt=timezone.now()
            )
            return cache_obj.cache_data
        except cls.DoesNotExist:
            # Cache miss or expired, get fresh data
            data = data_func()
            expires_at = timezone.now() + timedelta(seconds=timeout)
            
            # Update or create cache entry
            cls.objects.update_or_create(
                cache_key=key,
                defaults={
                    'cache_data': data,
                    'expires_at': expires_at
                }
            )
            return data

    @classmethod
    def invalidate(cls, key_pattern=None):
        """Invalidate cache entries"""
        if key_pattern:
            cls.objects.filter(cache_key__contains=key_pattern).delete()
        else:
            cls.objects.all().delete()


class DashboardAnalytics(models.Model):
    """Track dashboard usage analytics"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    page_view = models.CharField(max_length=100)
    widget_interactions = models.JSONField(default=dict)
    session_duration = models.PositiveIntegerField(null=True, blank=True)  # in seconds
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]

    @classmethod
    def track_page_view(cls, user, page):
        """Track a page view"""
        return cls.objects.create(user=user, page_view=page)

    @classmethod
    def track_widget_interaction(cls, user, widget_name, action):
        """Track widget interaction"""
        today = timezone.now().date()
        analytics, created = cls.objects.get_or_create(
            user=user,
            timestamp__date=today,
            defaults={'page_view': 'dashboard', 'widget_interactions': {}}
        )
        
        if widget_name not in analytics.widget_interactions:
            analytics.widget_interactions[widget_name] = {}
        
        if action not in analytics.widget_interactions[widget_name]:
            analytics.widget_interactions[widget_name][action] = 0
        
        analytics.widget_interactions[widget_name][action] += 1
        analytics.save()
