from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.accounts'
    label = 'accounts'
    
    def ready(self):
        # Import signals to attach login handler
        try:
            from . import signals  # noqa: F401
        except Exception:
            pass
