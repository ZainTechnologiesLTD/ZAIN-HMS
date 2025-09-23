# System Update Model for Version Management
# apps/core/models.py - Add this to your existing models

from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()

class SystemUpdate(models.Model):
    """Track available system updates"""
    
    PRIORITY_CHOICES = [
        ('low', 'Low Priority'),
        ('medium', 'Medium Priority'), 
        ('high', 'High Priority'),
        ('critical', 'Critical Security Update'),
    ]
    
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('downloading', 'Downloading'),
        ('installing', 'Installing'),
        ('installed', 'Installed'),
        ('failed', 'Failed'),
        ('skipped', 'Skipped'),
    ]
    
    version = models.CharField(max_length=50, unique=True)
    current_version = models.CharField(max_length=50)
    release_notes = models.TextField(blank=True)
    release_url = models.URLField(blank=True)
    published_at = models.DateTimeField()
    discovered_at = models.DateTimeField(auto_now_add=True)
    
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    
    is_critical = models.BooleanField(default=False)
    requires_downtime = models.BooleanField(default=False)
    
    notification_sent = models.BooleanField(default=False)
    auto_update_eligible = models.BooleanField(default=True)
    
    # Installation tracking
    installed_at = models.DateTimeField(null=True, blank=True)
    installed_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    installation_notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-published_at']
        verbose_name = "System Update"
        verbose_name_plural = "System Updates"
    
    def __str__(self):
        return f"ZAIN HMS {self.version} ({'Critical' if self.is_critical else self.priority.title()})"
    
    @property
    def is_newer_than_current(self):
        """Check if this version is newer than current"""
        try:
            current_parts = [int(x) for x in self.current_version.split('.')]
            new_parts = [int(x) for x in self.version.split('.')]
            return new_parts > current_parts
        except (ValueError, AttributeError):
            return True
    
    @property 
    def age_days(self):
        """Days since update was published"""
        return (timezone.now() - self.published_at).days


class UpdateNotification(models.Model):
    """Track notifications sent to users about updates"""
    
    update = models.ForeignKey(SystemUpdate, on_delete=models.CASCADE, related_name='notifications')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    sent_at = models.DateTimeField(auto_now_add=True)
    viewed_at = models.DateTimeField(null=True, blank=True)
    dismissed_at = models.DateTimeField(null=True, blank=True)
    
    notification_type = models.CharField(max_length=50, default='update_available')
    
    class Meta:
        unique_together = ['update', 'user']
        ordering = ['-sent_at']
    
    def mark_viewed(self):
        """Mark notification as viewed"""
        if not self.viewed_at:
            self.viewed_at = timezone.now()
            self.save(update_fields=['viewed_at'])
    
    def dismiss(self):
        """Mark notification as dismissed"""
        self.dismissed_at = timezone.now()
        self.save(update_fields=['dismissed_at'])


class DeploymentLog(models.Model):
    """Track deployment history and results"""
    
    version = models.CharField(max_length=50)
    previous_version = models.CharField(max_length=50, blank=True)
    
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    initiated_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    
    status = models.CharField(max_length=20, choices=[
        ('started', 'Started'),
        ('success', 'Successful'),
        ('failed', 'Failed'),
        ('rolled_back', 'Rolled Back'),
    ], default='started')
    
    log_output = models.TextField(blank=True)
    error_message = models.TextField(blank=True)
    
    # Deployment metrics
    downtime_seconds = models.IntegerField(null=True, blank=True)
    backup_size_mb = models.FloatField(null=True, blank=True)
    
    class Meta:
        ordering = ['-started_at']
        verbose_name = "Deployment Log"
        verbose_name_plural = "Deployment Logs"
    
    def __str__(self):
        return f"Deploy {self.version} - {self.status} ({self.started_at.strftime('%Y-%m-%d %H:%M')})"
    
    @property
    def duration_minutes(self):
        """Calculate deployment duration in minutes"""
        if self.completed_at:
            return round((self.completed_at - self.started_at).total_seconds() / 60, 2)
        return None