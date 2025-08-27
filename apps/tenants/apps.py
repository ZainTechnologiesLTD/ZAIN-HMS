from django.apps import AppConfig

class TenantsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.tenants'
    verbose_name = 'Hospital Tenants'
    
    def ready(self):
        """Import signals when the app is ready"""
        import apps.tenants.signals
