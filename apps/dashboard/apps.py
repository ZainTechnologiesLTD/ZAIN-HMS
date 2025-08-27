from django.apps import AppConfig


class DashboardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.dashboard'
    label = 'apps_dashboard'  # Unique label to avoid conflict with jet.dashboard
