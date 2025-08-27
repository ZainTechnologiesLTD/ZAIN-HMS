# apps/tenants/signals.py
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.contrib import messages
from .models import Tenant
from .utils import AllowedHostsManager
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Tenant)
def create_hospital_database_signal(sender, instance, created, **kwargs):
    """
    Automatically create hospital database and configure ALLOWED_HOSTS when a new hospital is created
    This ensures setup even if created outside the admin interface
    """
    if created:  # Only for new hospitals
        try:
            from apps.core.db_router import TenantDatabaseManager
            hospital_code = instance.subdomain
            
            # Add hospital subdomain to ALLOWED_HOSTS
            AllowedHostsManager.add_hospital_domain(hospital_code)
            
            # Create the hospital database with all necessary modules
            TenantDatabaseManager.create_hospital_database(hospital_code)
            
            logger.info(
                f"Hospital created successfully: {instance.name} "
                f"(hospital_{hospital_code}, domain: {hospital_code}.localhost)"
            )
            
        except Exception as e:
            logger.error(
                f"Failed to create hospital setup for {instance.name}: {str(e)}"
            )
            # Don't raise the exception to prevent hospital creation failure
            # The admin interface will handle showing error messages

@receiver(pre_delete, sender=Tenant)
def remove_hospital_domain_signal(sender, instance, **kwargs):
    """
    Remove hospital domain from ALLOWED_HOSTS when hospital is deleted
    """
    try:
        hospital_code = instance.subdomain
        
        # Remove hospital subdomain from ALLOWED_HOSTS
        AllowedHostsManager.remove_hospital_domain(hospital_code)
        
        logger.info(
            f"Hospital domain removed from ALLOWED_HOSTS: {instance.name} "
            f"({hospital_code}.localhost)"
        )
        
    except Exception as e:
        logger.error(
            f"Failed to remove hospital domain for {instance.name}: {str(e)}"
        )
