from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.accounts'
    label = 'accounts'
    
    def ready(self):
        # Import signals to attach login handler
        try:
            from . import signals  # noqa: F401

        except Exception as e:
            # Log but don't fail app startup
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to configure authentication signals: {str(e)}")
            # Also print to console for debugging
            print(f"❌ Failed to configure authentication signals: {str(e)}")
            pass
