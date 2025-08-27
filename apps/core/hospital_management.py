# Enhanced Hospital Admin Management System
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from apps.accounts.models import CustomUser as User
import uuid


class Hospital(models.Model):
    """Enhanced Hospital model for multi-tenant system"""
    # Basic Information
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True, help_text="Unique hospital identifier")
    registration_number = models.CharField(max_length=100, unique=True)
    
    # Contact Information
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    website = models.URLField(blank=True)
    
    # Address
    address_line_1 = models.CharField(max_length=200)
    address_line_2 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='Bangladesh')
    postal_code = models.CharField(max_length=20)
    
    # Hospital Classification
    HOSPITAL_TYPES = [
        ('government', 'Government Hospital'),
        ('private', 'Private Hospital'),
        ('specialized', 'Specialized Hospital'),
        ('clinic', 'Clinic'),
        ('diagnostic', 'Diagnostic Center'),
    ]
    hospital_type = models.CharField(max_length=50, choices=HOSPITAL_TYPES)
    
    # Capacity and Services
    bed_capacity = models.PositiveIntegerField(default=0)
    total_staff = models.PositiveIntegerField(default=0)
    
    # Hospital Admin
    primary_admin = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='administered_hospitals',
        help_text="Primary hospital administrator"
    )
    
    # System Settings
    database_name = models.CharField(max_length=100, unique=True, help_text="Database identifier for this hospital")
    is_active = models.BooleanField(default=True)
    subscription_status = models.CharField(max_length=50, choices=[
        ('trial', 'Trial'),
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('expired', 'Expired'),
    ], default='trial')
    
    # Billing and Subscription
    subscription_start = models.DateField(null=True, blank=True)
    subscription_end = models.DateField(null=True, blank=True)
    monthly_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Features and Modules
    enabled_modules = models.JSONField(default=dict, help_text="Enabled modules for this hospital")
    custom_settings = models.JSONField(default=dict, help_text="Hospital-specific settings")
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_hospitals')
    
    class Meta:
        ordering = ['name']
        verbose_name_plural = "Hospitals"
        
    def __str__(self):
        return f"{self.code} - {self.name}"
        
    def get_admin_users(self):
        """Get all admin users for this hospital"""
        return User.objects.filter(
            hospital_access__hospital=self,
            hospital_access__role__in=['HOSPITAL_ADMIN', 'ADMIN']
        )
        
    def get_total_users(self):
        """Get total user count for this hospital"""
        return User.objects.filter(hospital_access__hospital=self).count()


class HospitalUserAccess(models.Model):
    """Manages user access permissions for specific hospitals"""
    HOSPITAL_ROLES = [
        ('HOSPITAL_ADMIN', 'Hospital Administrator'),
        ('DOCTOR', 'Doctor'),
        ('NURSE', 'Nurse'),
        ('LAB_TECHNICIAN', 'Laboratory Technician'),
        ('PHARMACIST', 'Pharmacist'),
        ('RADIOLOGIST', 'Radiologist'),
        ('RECEPTIONIST', 'Receptionist'),
        ('BILLING_STAFF', 'Billing Staff'),
        ('STAFF', 'General Staff'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hospital_access')
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='user_access')
    role = models.CharField(max_length=50, choices=HOSPITAL_ROLES)
    
    # Permissions
    can_add_users = models.BooleanField(default=False)
    can_edit_users = models.BooleanField(default=False)
    can_delete_users = models.BooleanField(default=False)
    can_access_billing = models.BooleanField(default=False)
    can_access_reports = models.BooleanField(default=False)
    can_manage_inventory = models.BooleanField(default=False)
    
    # Department/Module Access
    accessible_modules = models.JSONField(default=list, help_text="List of modules this user can access")
    department_restrictions = models.JSONField(default=list, help_text="Specific departments user can access")
    
    # Status
    is_active = models.BooleanField(default=True)
    access_granted_at = models.DateTimeField(auto_now_add=True)
    access_granted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='granted_access')
    last_login_hospital = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['user', 'hospital']
        ordering = ['hospital', 'role', 'user']
        
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.hospital.name} ({self.role})"


class HospitalModule(models.Model):
    """Available modules/features for hospitals"""
    MODULE_TYPES = [
        ('appointments', 'Appointment Management'),
        ('patients', 'Patient Management'),
        ('billing', 'Billing & Invoicing'),
        ('laboratory', 'Laboratory Management'),
        ('pharmacy', 'Pharmacy Management'),
        ('radiology', 'Radiology Management'),
        ('emergency', 'Emergency Management'),
        ('surgery', 'Surgery Management'),
        ('ipd', 'In-Patient Department'),
        ('opd', 'Out-Patient Department'),
        ('inventory', 'Inventory Management'),
        ('hr', 'Human Resources'),
        ('reports', 'Reports & Analytics'),
        ('telemedicine', 'Telemedicine'),
    ]
    
    name = models.CharField(max_length=100)
    module_type = models.CharField(max_length=50, choices=MODULE_TYPES, unique=True)
    description = models.TextField()
    icon = models.CharField(max_length=50, blank=True)
    
    # Pricing and Features
    is_premium = models.BooleanField(default=False)
    monthly_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    features = models.JSONField(default=list, help_text="List of features in this module")
    
    # Dependencies
    required_modules = models.ManyToManyField('self', blank=True, symmetrical=False)
    
    # Status
    is_active = models.BooleanField(default=True)
    version = models.CharField(max_length=20, default='1.0.0')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        
    def __str__(self):
        return self.name


class HospitalSettings(models.Model):
    """Hospital-specific configuration settings"""
    hospital = models.OneToOneField(Hospital, on_delete=models.CASCADE, related_name='settings')
    
    # Branding
    logo = models.ImageField(upload_to='hospital_logos/', blank=True)
    color_scheme = models.CharField(max_length=50, default='blue')
    custom_css = models.TextField(blank=True)
    
    # Operational Settings
    working_hours_start = models.TimeField(default='08:00')
    working_hours_end = models.TimeField(default='18:00')
    appointment_duration = models.PositiveIntegerField(default=30, help_text="Default appointment duration in minutes")
    max_appointments_per_day = models.PositiveIntegerField(default=50)
    
    # Notification Settings
    enable_sms_notifications = models.BooleanField(default=False)
    enable_email_notifications = models.BooleanField(default=True)
    sms_api_key = models.CharField(max_length=200, blank=True)
    email_from_address = models.EmailField(blank=True)
    
    # Financial Settings
    default_currency = models.CharField(max_length=10, default='BDT')
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    # System Settings
    backup_frequency = models.CharField(max_length=20, choices=[
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ], default='weekly')
    
    data_retention_days = models.PositiveIntegerField(default=2555, help_text="Days to retain data (7 years default)")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Settings for {self.hospital.name}"
