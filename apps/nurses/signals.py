from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User, Group
from django.core.mail import send_mail
from django.conf import settings
from .models import Nurse, NurseLeave

@receiver(post_save, sender=Nurse)
def create_nurse_group(sender, instance, created, **kwargs):
    """Add nurse to the 'Nurses' group when created"""
    if created:
        nurse_group, _ = Group.objects.get_or_create(name='Nurses')
        instance.user.groups.add(nurse_group)

@receiver(post_save, sender=NurseLeave)
def notify_leave_status(sender, instance, created, **kwargs):
    """Send email notifications for leave requests and status changes"""
    if created:
        # Notify admin about new leave request
        subject = f'New Leave Request from {instance.nurse}'
        message = f"""
        New leave request details:
        Nurse: {instance.nurse}
        Type: {instance.get_leave_type_display()}
        From: {instance.start_date}
        To: {instance.end_date}
        Reason: {instance.reason}
        """
        admin_email = settings.ADMIN_EMAIL
        if admin_email:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [admin_email],
                fail_silently=True,
            )
    
    elif instance.status in ['approved', 'rejected']:
        # Notify nurse about leave request status
        subject = f'Leave Request {instance.status.title()}'
        message = f"""
        Your leave request has been {instance.status}:
        Type: {instance.get_leave_type_display()}
        From: {instance.start_date}
        To: {instance.end_date}
        
        Status updated by: {instance.approved_by}
        """
        if instance.nurse.user.email:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [instance.nurse.user.email],
                fail_silently=True,
            )

@receiver(pre_save, sender=Nurse)
def update_nurse_status(sender, instance, **kwargs):
    """Update nurse active status based on joining date"""
    try:
        old_instance = Nurse.objects.get(pk=instance.pk)
        if old_instance.is_active != instance.is_active:
            # Send notification about status change
            subject = f'Nurse Status Update - {instance}'
            message = f"""
            The status of nurse {instance} has been changed to {'Active' if instance.is_active else 'Inactive'}.
            """
            admin_email = settings.ADMIN_EMAIL
            if admin_email:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [admin_email],
                    fail_silently=True,
                )
    except Nurse.DoesNotExist:
        pass  # This is a new instance