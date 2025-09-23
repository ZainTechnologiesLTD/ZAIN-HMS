# notifications/models.py
from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from apps.patients.models import Patient
import uuid


class Notification(models.Model):
    LEVELS = (
        ('info', 'Information'),
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('error', 'Error'),
    )
    
    recipient = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    level = models.CharField(max_length=10, choices=LEVELS)
    title = models.CharField(max_length=250)
    message = models.TextField()
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # For linking to related objects (e.g., appointments, patients)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    action_url = models.CharField(max_length=200, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.recipient.username} - {self.title}"


class NotificationTemplate(models.Model):
    """Templates for different types of document notifications"""
    
    DOCUMENT_TYPES = [
        ('BILL', 'Bill/Invoice'),
        ('PRESCRIPTION', 'Prescription'),
        ('DIAGNOSTIC_REPORT', 'Diagnostic Report'),
        ('APPOINTMENT', 'Appointment'),
        ('LAB_RESULT', 'Lab Result'),
        ('DISCHARGE_SUMMARY', 'Discharge Summary'),
        ('MEDICAL_CERTIFICATE', 'Medical Certificate'),
        ('PHARMACY_BILL', 'Pharmacy Bill'),
    ]
    
    DELIVERY_CHANNELS = [
        ('EMAIL', 'Email'),
        ('WHATSAPP', 'WhatsApp'),
        ('TELEGRAM', 'Telegram'),
        ('SMS', 'SMS'),
    ]
    
    name = models.CharField(max_length=100)
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    channel = models.CharField(max_length=20, choices=DELIVERY_CHANNELS)
    
    # Template Content
    subject_template = models.CharField(max_length=200, help_text="Email subject or message title")
    body_template = models.TextField(help_text="Message body with placeholders like {{patient_name}}, {{document_link}}")
    
    # Settings
    is_active = models.BooleanField(default=True)
    auto_send = models.BooleanField(default=True, help_text="Automatically send when document is created")
    send_delay_minutes = models.PositiveIntegerField(default=0, help_text="Delay before sending (0 = immediate)")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['document_type', 'channel']
        unique_together = ['document_type', 'channel']
    
    def __str__(self):
        return f"{self.get_document_type_display()} - {self.get_channel_display()}"


class PatientNotification(models.Model):
    """Track notifications sent to patients via multiple channels"""
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SENT', 'Sent'),
        ('DELIVERED', 'Delivered'),
        ('READ', 'Read'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='document_notifications')
    template = models.ForeignKey(NotificationTemplate, on_delete=models.CASCADE)
    
    # Document Reference (Generic Foreign Key)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    document = GenericForeignKey('content_type', 'object_id')
    
    # Delivery Details
    recipient_email = models.EmailField(blank=True)
    recipient_phone = models.CharField(max_length=20, blank=True)
    recipient_whatsapp = models.CharField(max_length=20, blank=True)
    recipient_telegram = models.CharField(max_length=50, blank=True)
    
    # Content
    subject = models.CharField(max_length=200)
    message_body = models.TextField()
    document_url = models.URLField(blank=True)
    attachment_path = models.CharField(max_length=500, blank=True)
    
    # Status Tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    scheduled_at = models.DateTimeField(default=timezone.now)
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    
    # Error Tracking
    error_message = models.TextField(blank=True)
    retry_count = models.PositiveIntegerField(default=0)
    max_retries = models.PositiveIntegerField(default=3)
    
    # Metadata
    delivery_provider = models.CharField(max_length=50, blank=True, help_text="WhatsApp API, Telegram Bot, etc.")
    external_message_id = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.patient.get_full_name()} - {self.template.name} - {self.status}"


class NotificationSettings(models.Model):
    """System-wide notification settings for document delivery"""
    
    # Email Settings
    email_enabled = models.BooleanField(default=True)
    email_from_name = models.CharField(max_length=100, default="Hospital Management System")
    email_from_address = models.EmailField(blank=True)
    
    # WhatsApp Settings
    whatsapp_enabled = models.BooleanField(default=False)
    whatsapp_api_url = models.URLField(blank=True, help_text="WhatsApp Business API URL")
    whatsapp_api_key = models.CharField(max_length=200, blank=True)
    whatsapp_phone_number = models.CharField(max_length=20, blank=True)
    
    # Telegram Settings
    telegram_enabled = models.BooleanField(default=False)
    telegram_bot_token = models.CharField(max_length=200, blank=True)
    telegram_chat_id = models.CharField(max_length=50, blank=True)
    
    # SMS Settings
    sms_enabled = models.BooleanField(default=False)
    sms_api_url = models.URLField(blank=True)
    sms_api_key = models.CharField(max_length=200, blank=True)
    sms_sender_id = models.CharField(max_length=20, blank=True)
    
    # General Settings
    document_base_url = models.URLField(help_text="Base URL for document links", default="http://localhost:8000")
    auto_cleanup_days = models.PositiveIntegerField(default=90, help_text="Days to keep old notifications")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Notification Settings"
        verbose_name_plural = "Notification Settings"
    
    def __str__(self):
        return "Document Notification Settings"


class DeliveryLog(models.Model):
    """Detailed logs for notification delivery attempts"""
    
    notification = models.ForeignKey(PatientNotification, on_delete=models.CASCADE, related_name='delivery_logs')
    attempt_number = models.PositiveIntegerField()
    
    # Request Details
    api_endpoint = models.URLField(blank=True)
    request_payload = models.TextField(blank=True)
    
    # Response Details
    response_status_code = models.PositiveIntegerField(null=True)
    response_body = models.TextField(blank=True)
    
    # Outcome
    success = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)
    
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"Attempt {self.attempt_number} - {'Success' if self.success else 'Failed'}"
