# apps/accounts/signals.py
# Simple stub signals file for authentication

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User

@receiver(post_save, sender=User)
def user_created(sender, instance, created, **kwargs):
    """Handle user creation"""
    if created:
        # Simple user creation logic for ZAIN HMS
        pass