# apps/reports/models.py
from django.db import models
from django.contrib.auth import get_user_model
# # from tenants.models import  # Temporarily commented Tenant  # Temporarily commented
import uuid

User = get_user_model()


class Report(models.Model):
    """Generated reports"""
    REPORT_TYPES = [
        ('PATIENT', 'Patient Report'),
        ('APPOINTMENT', 'Appointment Report'),
        ('BILLING', 'Billing Report'),
        ('DOCTOR', 'Doctor Report'),
        ('DEPARTMENT', 'Department Report'),
        ('FINANCIAL', 'Financial Report'),
        ('INVENTORY', 'Inventory Report'),
        ('LABORATORY', 'Laboratory Report'),
        ('EMERGENCY', 'Emergency Report'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]
    
    FORMAT_CHOICES = [
        ('PDF', 'PDF'),
        ('EXCEL', 'Excel'),
        ('CSV', 'CSV'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # tenant = models.ForeignKey(Tenant  # Temporarily commented, on_delete=models.CASCADE, related_name='reports')
    generated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='generated_reports')
    
    name = models.CharField(max_length=200)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES, default='PDF')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # Date range for the report
    date_from = models.DateField(null=True, blank=True)
    date_to = models.DateField(null=True, blank=True)
    
    # Filters applied
    filters = models.JSONField(default=dict, blank=True)
    
    # Generated file
    file = models.FileField(upload_to='reports/%Y/%m/', null=True, blank=True)
    
    # Metadata
    total_records = models.PositiveIntegerField(default=0)
    file_size = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        """Override save to handle cross-database relationships"""
        using = kwargs.get('using', 'default')
        
        # If saving to a tenant database, temporarily disable foreign key checks
        if using and using != 'default':
            from django.db import connections
            connection = connections[using]
            with connection.cursor() as cursor:
                cursor.execute("PRAGMA foreign_keys=OFF")
                try:
                    super().save(*args, **kwargs)
                finally:
                    cursor.execute("PRAGMA foreign_keys=ON")
        else:
            super().save(*args, **kwargs)
    
    def delete(self, using=None, keep_parents=False):
        """Override delete to handle cross-database relationships"""
        if using and using != 'default':
            from django.db import connections
            connection = connections[using]
            with connection.cursor() as cursor:
                cursor.execute("PRAGMA foreign_keys=OFF")
                try:
                    super().delete(using=using, keep_parents=keep_parents)
                finally:
                    cursor.execute("PRAGMA foreign_keys=ON")
        else:
            super().delete(using=using, keep_parents=keep_parents)
    
    def __str__(self):
        return f"{self.name} - {self.get_report_type_display()}"


class ReportTemplate(models.Model):
    """Predefined report templates"""
    # tenant = models.ForeignKey(Tenant  # Temporarily commented, on_delete=models.CASCADE, related_name='report_templates')
    name = models.CharField(max_length=200)
    report_type = models.CharField(max_length=20, choices=Report.REPORT_TYPES)
    description = models.TextField(blank=True)
    
    # Template configuration
    columns = models.JSONField(default=list)  # List of columns to include
    default_filters = models.JSONField(default=dict)  # Default filter values
    chart_config = models.JSONField(default=dict, blank=True)  # Chart configuration if applicable
    
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_templates')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def save(self, *args, **kwargs):
        """Override save to handle cross-database relationships"""
        using = kwargs.get('using', 'default')
        
        # If saving to a tenant database, temporarily disable foreign key checks
        if using and using != 'default':
            from django.db import connections
            connection = connections[using]
            with connection.cursor() as cursor:
                cursor.execute("PRAGMA foreign_keys=OFF")
                try:
                    super().save(*args, **kwargs)
                finally:
                    cursor.execute("PRAGMA foreign_keys=ON")
        else:
            super().save(*args, **kwargs)
    
    def delete(self, using=None, keep_parents=False):
        """Override delete to handle cross-database relationships"""
        if using and using != 'default':
            from django.db import connections
            connection = connections[using]
            with connection.cursor() as cursor:
                cursor.execute("PRAGMA foreign_keys=OFF")
                try:
                    super().delete(using=using, keep_parents=keep_parents)
                finally:
                    cursor.execute("PRAGMA foreign_keys=ON")
        else:
            super().delete(using=using, keep_parents=keep_parents)

    def __str__(self):
        return self.name
