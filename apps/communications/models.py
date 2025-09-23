# Communication tracking models
from django.db import models
from django.utils import timezone
from apps.appointments.models import Appointment
from apps.patients.models import Patient
from apps.accounts.models import CustomUser as User


class CommunicationLog(models.Model):
    """Track all communications sent to patients"""
    CHANNEL_CHOICES = [
        ('whatsapp', 'WhatsApp'),
        ('telegram', 'Telegram'),
        ('viber', 'Viber'),
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('voice', 'Voice Call'),
    ]

    STATUS_CHOICES = [
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('read', 'Read'),
        ('failed', 'Failed'),
        ('pending', 'Pending'),
    ]

    TEMPLATE_CHOICES = [
        ('reminder', 'Appointment Reminder'),
        ('confirmation', 'Appointment Confirmation'),
        ('cancellation', 'Appointment Cancellation'),
        ('reschedule', 'Reschedule Notice'),
        ('follow_up', 'Follow-up Reminder'),
        ('custom', 'Custom Message'),
    ]

    # Basic Information
    appointment = models.ForeignKey(
        Appointment, 
        on_delete=models.CASCADE, 
        related_name='communications'
    )
    patient = models.ForeignKey(
        Patient, 
        on_delete=models.CASCADE, 
        related_name='communications'
    )
    sent_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='sent_communications'
    )

    # Communication Details
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES)
    template_type = models.CharField(max_length=20, choices=TEMPLATE_CHOICES, default='reminder')
    recipient_phone = models.CharField(max_length=20, blank=True)
    recipient_email = models.EmailField(blank=True)
    
    # Message Content
    message = models.TextField(help_text="Actual message sent")
    subject = models.CharField(max_length=200, blank=True, help_text="Email subject or message title")
    
    # Status Tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    sent_at = models.DateTimeField(auto_now_add=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    
    # Error Tracking
    error_message = models.TextField(blank=True, help_text="Error details if failed")
    retry_count = models.PositiveIntegerField(default=0)
    
    # Metadata
    external_id = models.CharField(max_length=100, blank=True, help_text="External service message ID")
    user_agent = models.TextField(blank=True, help_text="Browser/device info")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        ordering = ['-sent_at']
        indexes = [
            models.Index(fields=['appointment', 'channel']),
            models.Index(fields=['patient', 'sent_at']),
            models.Index(fields=['status', 'sent_at']),
        ]

    def __str__(self):
        return f"{self.channel} to {self.patient} - {self.status}"

    def mark_delivered(self):
        """Mark communication as delivered"""
        if self.status == 'sent':
            self.status = 'delivered'
            self.delivered_at = timezone.now()
            self.save(update_fields=['status', 'delivered_at'])

    def mark_read(self):
        """Mark communication as read"""
        if self.status in ['sent', 'delivered']:
            self.status = 'read'
            self.read_at = timezone.now()
            self.save(update_fields=['status', 'read_at'])

    def mark_failed(self, error_message=""):
        """Mark communication as failed"""
        self.status = 'failed'
        self.failed_at = timezone.now()
        if error_message:
            self.error_message = error_message
        self.save(update_fields=['status', 'failed_at', 'error_message'])


class CommunicationTemplate(models.Model):
    """Reusable message templates"""
    name = models.CharField(max_length=100, unique=True)
    template_type = models.CharField(
        max_length=20, 
        choices=CommunicationLog.TEMPLATE_CHOICES
    )
    channel = models.CharField(
        max_length=20, 
        choices=CommunicationLog.CHANNEL_CHOICES
    )
    
    subject_template = models.CharField(
        max_length=200, 
        blank=True, 
        help_text="Template for email subject (supports variables)"
    )
    message_template = models.TextField(
        help_text="Message template with variables: {patient_name}, {doctor_name}, {appointment_date}, etc."
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['template_type', 'channel']

    def __str__(self):
        return f"{self.name} ({self.channel})"

    def render(self, context):
        """Render template with context variables"""
        try:
            message = self.message_template.format(**context)
            subject = self.subject_template.format(**context) if self.subject_template else ""
            return subject, message
        except KeyError as e:
            raise ValueError(f"Missing template variable: {e}")


class PatientCommunicationPreference(models.Model):
    """Patient communication preferences and opt-outs"""
    patient = models.OneToOneField(
        Patient, 
        on_delete=models.CASCADE, 
        related_name='communication_preferences'
    )
    
    # Channel preferences
    allow_whatsapp = models.BooleanField(default=True)
    allow_telegram = models.BooleanField(default=True)
    allow_viber = models.BooleanField(default=True)
    allow_email = models.BooleanField(default=True)
    allow_sms = models.BooleanField(default=True)
    allow_voice = models.BooleanField(default=True)
    
    # Timing preferences
    preferred_time_start = models.TimeField(default='09:00')
    preferred_time_end = models.TimeField(default='18:00')
    timezone = models.CharField(max_length=50, default='UTC')
    
    # Language preference
    preferred_language = models.CharField(max_length=10, default='en')
    
    # Reminder preferences
    reminder_advance_hours = models.PositiveIntegerField(
        default=24, 
        help_text="Hours before appointment to send reminder"
    )
    send_confirmation = models.BooleanField(default=True)
    send_reminder = models.BooleanField(default=True)
    send_follow_up = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def can_receive(self, channel):
        """Check if patient allows communication via channel"""
        channel_map = {
            'whatsapp': self.allow_whatsapp,
            'telegram': self.allow_telegram,
            'viber': self.allow_viber,
            'email': self.allow_email,
            'sms': self.allow_sms,
            'voice': self.allow_voice,
        }
        return channel_map.get(channel, False)

    def __str__(self):
        return f"Communication preferences for {self.patient}"
