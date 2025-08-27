from django.apps import AppConfig
import threading
from django.db import connection


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'
    
    def ready(self):
        """Called when Django is ready - Setup deferred database loading"""
        # Import signals for automatic database creation
        try:
            import apps.tenants.signals
        except ImportError:
            pass
            
        # Defer database queries to avoid initialization warnings
        # Use a thread to load hospital data after Django is fully ready
        def load_hospital_data():
            try:
                # Wait for Django to be fully initialized
                threading.Event().wait(2)
                
                # Load hospital databases
                from .db_router import TenantDatabaseManager
                TenantDatabaseManager.discover_and_load_hospital_databases()
                
                # Load hospital domains to ALLOWED_HOSTS
                from apps.tenants.utils import AllowedHostsManager
                AllowedHostsManager.load_hospital_domains()
                
            except Exception as e:
                print(f"Warning: Could not load hospital data: {e}")
        
        # Start loading in background thread
        thread = threading.Thread(target=load_hospital_data, daemon=True)
        thread.start()
