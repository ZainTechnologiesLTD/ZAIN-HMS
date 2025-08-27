# apps/radiology/apps.py
from django.apps import AppConfig


class RadiologyConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.tenants.radiology'
    verbose_name = 'Tenant Radiology Management'
    verbose_name = 'Radiology Department'
    
    def ready(self):
        # Import signal handlers when app is ready
        try:
            import apps.tenants.radiology.signals  # noqa
        except ImportError:
            pass
