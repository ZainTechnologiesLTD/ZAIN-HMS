# apps/core/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
# # # # from tenants.models import  # Temporarily commented Tenant  # Temporarily commented  # Temporarily commented
import uuid

User = get_user_model()


class BaseTenantModel(models.Model):
    """
    Abstract base model for all tenant-specific models
    Automatically handles tenant context and provides common fields
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # # # tenant = models.ForeignKey(Tenant  # Temporarily commented, on_delete=models.CASCADE)  # Temporarily commented
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    
    class Meta:
        abstract = True
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        # Auto-set tenant from request context if not set
        if not self.tenant_id and hasattr(self, '_current_tenant'):
            self.tenant = self._current_tenant
        super().save(*args, **kwargs)


class TenantFilteredManager(models.Manager):
    """
    Manager that automatically filters by tenant context
    """
    def get_queryset(self):
        qs = super().get_queryset()
        return qs


class ActivityLog(models.Model):
    """Track all user activities in the system"""
    ACTION_CHOICES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('VIEW', 'View'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('EXPORT', 'Export'),
        ('IMPORT', 'Import'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # # # tenant = models.ForeignKey(Tenant  # Temporarily commented, on_delete=models.CASCADE, related_name='activity_logs')  # Temporarily commented
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100, null=True, blank=True)
    object_repr = models.CharField(max_length=200)
    changes = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            # # models.Index(fields=['tenant', '-timestamp']),  # Temporarily commented
  # Temporarily commented
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['action', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user} {self.action} {self.model_name} at {self.timestamp}"


class SystemConfiguration(models.Model):
    """System-wide configuration settings"""
    # # tenant = models.OneToOneField(Tenant  # Temporarily commented, on_delete=models.CASCADE, related_name='system_configuration')
    
    # General Settings
    tenant_name = models.CharField(max_length=200)
    tenant_logo = models.ImageField(upload_to='tenant/logos/', null=True, blank=True)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=17)
    address = models.TextField()
    
    # Business Settings
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    currency_code = models.CharField(max_length=3, default='USD')
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    # Appointment Settings
    appointment_duration = models.PositiveIntegerField(default=30)  # minutes
    advance_booking_days = models.PositiveIntegerField(default=30)
    cancellation_hours = models.PositiveIntegerField(default=24)
    
    # Patient Settings
    patient_id_prefix = models.CharField(max_length=10, default='PAT')
    auto_generate_patient_id = models.BooleanField(default=True)
    
    # Notification Settings
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    whatsapp_notifications = models.BooleanField(default=False)
    
    # Backup Settings
    auto_backup = models.BooleanField(default=True)
    backup_frequency = models.CharField(
        max_length=20,
        choices=[
            ('DAILY', 'Daily'),
            ('WEEKLY', 'Weekly'),
            ('MONTHLY', 'Monthly'),
        ],
        default='DAILY'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Configuration for {self.tenant_name}"


class Notification(models.Model):
    """System notifications"""
    TYPE_CHOICES = [
        ('INFO', 'Information'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('SUCCESS', 'Success'),
        ('APPOINTMENT', 'Appointment'),
        ('BILLING', 'Billing'),
        ('SYSTEM', 'System'),
        ('LAB_RESULT', 'Lab Result'),
        ('PRESCRIPTION', 'Prescription'),
        ('EMERGENCY', 'Emergency'),
        ('REMINDER', 'Reminder'),
    ]
    
    PRIORITY_LEVELS = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # # tenant = models.ForeignKey(Tenant  # Temporarily commented, on_delete=models.CASCADE, related_name='notifications')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_notifications')
    
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='INFO')
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='MEDIUM')
    title = models.CharField(max_length=200)
    message = models.TextField()
    data = models.JSONField(default=dict, blank=True)  # Additional data for the notification
    link = models.CharField(max_length=500, blank=True)
    
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read', '-created_at']),
            # # models.Index(fields=['tenant', '-created_at']),  # Temporarily commented
  # Temporarily commented
        ]
    
    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
    
    def __str__(self):
        return f"{self.title} - {self.recipient.get_full_name()}"


class FileUpload(models.Model):
    """Track uploaded files"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # # tenant = models.ForeignKey(Tenant  # Temporarily commented, on_delete=models.CASCADE, related_name='file_uploads')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_files')
    
    file = models.FileField(upload_to='uploads/%Y/%m/%d/')
    original_name = models.CharField(max_length=255)
    file_size = models.PositiveBigIntegerField()
    content_type = models.CharField(max_length=100)
    
    # Optional association with other models
    content_type_model = models.CharField(max_length=100, null=True, blank=True)
    object_id = models.CharField(max_length=100, null=True, blank=True)
    
    description = models.TextField(blank=True)
    is_public = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.original_name} - {self.uploaded_by.get_full_name()}"


class SystemSetting(models.Model):
    """Key-value system settings"""
    # # tenant = models.ForeignKey(Tenant  # Temporarily commented, on_delete=models.CASCADE, related_name='system_settings')
    key = models.CharField(max_length=100)
    value = models.TextField()
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        constraints = []
    
    def __str__(self):
        return f"{self.key}: {self.value[:50]}"