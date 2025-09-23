from django.apps import AppConfig
import threading
from django.db import connection
import sys


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'
    
    def ready(self):
        """Called when Django is ready - ZAIN HMS unified system"""
        # ZAIN HMS - unified system, no need for deferred database loading
        pass
