from django.apps import AppConfig


class DashboardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.dashboard'
    verbose_name = 'Dashboard'
    
    def ready(self):
        """Import any signal handlers when the app is ready"""
        try:
            import apps.dashboard.signals  # noqa
        except ImportError:
            pass


class DashboardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.dashboard'
    label = 'apps_dashboard'  # Unique label to avoid conflict with jet.dashboard
