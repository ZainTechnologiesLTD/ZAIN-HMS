# apps/emr/apps.py
"""
EMR App Configuration
"""

from django.apps import AppConfig


class EmrConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.emr'
    verbose_name = 'Electronic Medical Records (EMR)'
    
    def ready(self):
        """Import signals when the app is ready"""
        try:
            from . import signals
        except ImportError:
            pass
