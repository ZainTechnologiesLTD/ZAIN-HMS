from django.apps import AppConfig


class CommunicationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.communications'
    verbose_name = 'Communications'

    def ready(self):
        # Import signals
        try:
            import apps.communications.signals
        except ImportError:
            pass
