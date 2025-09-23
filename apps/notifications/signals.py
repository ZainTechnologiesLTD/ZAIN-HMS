# apps/notifications/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.conf import settings
from .services import document_notification_manager
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender='billing.Invoice')
def send_bill_notification(sender, instance, created, **kwargs):
    """Send notification when a bill/invoice is created"""
    if created and instance.patient:
        try:
            # Generate document URL
            document_url = f"{getattr(settings, 'SITE_URL', 'http://localhost:8000')}/billing/invoice/{instance.id}/pdf/"
            
            document_notification_manager.send_document_notification(
                patient=instance.patient,
                document_type='BILL',
                document_obj=instance,
                document_url=document_url
            )
            
            logger.info(f"Bill notification triggered for invoice {instance.id}")
            
        except Exception as e:
            logger.error(f"Failed to send bill notification: {str(e)}")


@receiver(post_save, sender='appointments.Appointment')  
def send_appointment_notification(sender, instance, created, **kwargs):
    """Send notification when an appointment is created or updated"""
    if instance.patient:
        try:
            # Generate document URL  
            document_url = f"{getattr(settings, 'SITE_URL', 'http://localhost:8000')}/appointments/{instance.id}/"
            
            document_notification_manager.send_document_notification(
                patient=instance.patient,
                document_type='APPOINTMENT',
                document_obj=instance,
                document_url=document_url
            )
            
            action = "created" if created else "updated"
            logger.info(f"Appointment notification triggered for {action} appointment {instance.id}")
            
        except Exception as e:
            logger.error(f"Failed to send appointment notification: {str(e)}")


@receiver(post_save, sender='pharmacy.Prescription')
def send_prescription_notification(sender, instance, created, **kwargs):
    """Send notification when a prescription is created"""
    if created and instance.patient:
        try:
            # Generate document URL
            document_url = f"{getattr(settings, 'SITE_URL', 'http://localhost:8000')}/pharmacy/prescription/{instance.id}/pdf/"
            
            document_notification_manager.send_document_notification(
                patient=instance.patient,
                document_type='PRESCRIPTION',
                document_obj=instance,
                document_url=document_url
            )
            
            logger.info(f"Prescription notification triggered for prescription {instance.id}")
            
        except Exception as e:
            logger.error(f"Failed to send prescription notification: {str(e)}")


@receiver(post_save, sender='laboratory.LabTest')
def send_lab_result_notification(sender, instance, created, **kwargs):
    """Send notification when lab results are updated with results"""
    if instance.patient and instance.results:  # Only send when results are available
        try:
            # Generate document URL
            document_url = f"{getattr(settings, 'SITE_URL', 'http://localhost:8000')}/laboratory/test/{instance.id}/pdf/"
            
            document_notification_manager.send_document_notification(
                patient=instance.patient,
                document_type='LAB_RESULT',
                document_obj=instance,
                document_url=document_url
            )
            
            logger.info(f"Lab result notification triggered for test {instance.id}")
            
        except Exception as e:
            logger.error(f"Failed to send lab result notification: {str(e)}")


# Handle PoS Transaction notifications from billing module
@receiver(post_save, sender='billing.PoSTransaction')
def send_pos_transaction_notification(sender, instance, created, **kwargs):
    """Send notification when a PoS transaction is completed"""
    if created and instance.customer and instance.status == 'COMPLETED':
        try:
            # Generate receipt URL
            document_url = f"{getattr(settings, 'SITE_URL', 'http://localhost:8000')}/billing/pos/receipt/{instance.id}/pdf/"
            
            document_notification_manager.send_document_notification(
                patient=instance.customer,
                document_type='BILL',
                document_obj=instance,
                document_url=document_url
            )
            
            logger.info(f"PoS transaction notification triggered for transaction {instance.id}")
            
        except Exception as e:
            logger.error(f"Failed to send PoS transaction notification: {str(e)}")


# Future signals - will be activated when models exist
# Uncomment these when the respective models are available

# @receiver(post_save, sender='radiology.RadiologyExamination')
# def send_diagnostic_report_notification(sender, instance, created, **kwargs):
#     """Send notification when diagnostic/radiology reports are created"""
#     if created and instance.patient:
#         try:
#             document_url = f"{getattr(settings, 'SITE_URL', 'http://localhost:8000')}/radiology/report/{instance.id}/pdf/"
#             
#             document_notification_manager.send_document_notification(
#                 patient=instance.patient,
#                 document_type='DIAGNOSTIC_REPORT', 
#                 document_obj=instance,
#                 document_url=document_url
#             )
#             
#             logger.info(f"Diagnostic report notification triggered for report {instance.id}")
#             
#         except Exception as e:
#             logger.error(f"Failed to send diagnostic report notification: {str(e)}")


# @receiver(post_save, sender='ipd.DischargeRecord')
# def send_discharge_summary_notification(sender, instance, created, **kwargs):
#     """Send notification when discharge summary is created"""
#     if created and instance.patient:
#         try:
#             document_url = f"{getattr(settings, 'SITE_URL', 'http://localhost:8000')}/ipd/discharge/{instance.id}/pdf/"
#             
#             document_notification_manager.send_document_notification(
#                 patient=instance.patient,
#                 document_type='DISCHARGE_SUMMARY',
#                 document_obj=instance,
#                 document_url=document_url
#             )
#             
#             logger.info(f"Discharge summary notification triggered for record {instance.id}")
#             
#         except Exception as e:
#             logger.error(f"Failed to send discharge summary notification: {str(e)}")


# @receiver(post_save, sender='pharmacy.PharmacyBill')
# def send_pharmacy_bill_notification(sender, instance, created, **kwargs):
#     """Send notification when a pharmacy bill is created"""
#     if created and instance.patient:
#         try:
#             document_url = f"{getattr(settings, 'SITE_URL', 'http://localhost:8000')}/pharmacy/bill/{instance.id}/pdf/"
#             
#             document_notification_manager.send_document_notification(
#                 patient=instance.patient,
#                 document_type='PHARMACY_BILL',
#                 document_obj=instance,
#                 document_url=document_url
#             )
#             
#             logger.info(f"Pharmacy bill notification triggered for bill {instance.id}")
#             
#         except Exception as e:
#             logger.error(f"Failed to send pharmacy bill notification: {str(e)}")
