# apps/radiology/apps.py
from django.apps import AppConfig


class RadiologyConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.radiology'
    verbose_name = 'Radiology Department'
    
    def ready(self):
        # Import signal handlers when app is ready
        try:
            import apps.radiology.signals  # noqa
        except ImportError:
            pass
