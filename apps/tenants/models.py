from django.db import models
from django.conf import settings

class Tenant(models.Model):
    """
    SaaS Tenant model for multi-hospital system
    Each tenant represents a hospital with subscription and features
    """
    # Basic Information
    name = models.CharField(max_length=100, help_text="Hospital display name")
    subdomain = models.CharField(max_length=100, unique=True, help_text="Subdomain for hospital access")
    db_name = models.CharField(max_length=100, unique=True, help_text="Database name for this hospital")
    logo = models.ImageField(upload_to='hospital_logos/', blank=True, null=True, help_text="Hospital logo")
    admin = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, help_text="Hospital administrator")
    
    # Hospital Details
    address = models.TextField(blank=True, null=True, help_text="Hospital address")
    phone = models.CharField(max_length=20, blank=True, null=True, help_text="Hospital contact phone")
    email = models.EmailField(blank=True, null=True, help_text="Hospital contact email")
    website = models.URLField(blank=True, null=True, help_text="Hospital website")
    
    # SaaS Subscription Features
    SUBSCRIPTION_PLANS = [
        ('BASIC', 'Basic Plan - $99/month'),
        ('STANDARD', 'Standard Plan - $199/month'),
        ('PREMIUM', 'Premium Plan - $399/month'),
        ('ENTERPRISE', 'Enterprise Plan - $799/month'),
    ]
    
    subscription_plan = models.CharField(max_length=20, choices=SUBSCRIPTION_PLANS, default='BASIC', help_text="Subscription plan")
    subscription_start_date = models.DateTimeField(help_text="Subscription start date")
    subscription_end_date = models.DateTimeField(help_text="Subscription end date")
    trial_end_date = models.DateTimeField(blank=True, null=True, help_text="Trial period end date")
    is_trial = models.BooleanField(default=True, help_text="Whether hospital is in trial period")
    
    # Hospital Settings
    max_users = models.IntegerField(default=10, help_text="Maximum users allowed")
    max_patients = models.IntegerField(default=1000, help_text="Maximum patients allowed")
    max_storage_gb = models.IntegerField(default=5, help_text="Storage limit in GB")
    
    # Features Enabled
    telemedicine_enabled = models.BooleanField(default=False, help_text="Enable telemedicine module")
    laboratory_enabled = models.BooleanField(default=True, help_text="Enable laboratory module")
    radiology_enabled = models.BooleanField(default=True, help_text="Enable radiology module")
    pharmacy_enabled = models.BooleanField(default=True, help_text="Enable pharmacy module")
    billing_enabled = models.BooleanField(default=True, help_text="Enable billing module")
    ipd_enabled = models.BooleanField(default=False, help_text="Enable IPD module")
    emergency_enabled = models.BooleanField(default=False, help_text="Enable emergency module")
    
    # Status
    is_active = models.BooleanField(default=True, help_text="Whether hospital is active")
    is_suspended = models.BooleanField(default=False, help_text="Whether hospital is suspended")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'tenants_tenant'
        verbose_name = 'Hospital Tenant'
        verbose_name_plural = 'Hospital Tenants'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.subdomain}) - {self.get_subscription_plan_display()}"
    
    @property
    def full_domain(self):
        """Get full domain for this tenant"""
        return f"{self.subdomain}.localhost:8000"
    
    @property
    def hospital_url(self):
        """Get base URL for this hospital"""
        return f"http://{self.full_domain}"
    
    def get_module_url(self, module_name):
        """Get URL for specific module in this hospital"""
        return f"{self.hospital_url}/{module_name}/"
    
    @property
    def is_subscription_active(self):
        """Check if subscription is active"""
        from django.utils import timezone
        now = timezone.now()
        return self.is_active and not self.is_suspended and now <= self.subscription_end_date
    
    @property
    def days_until_expiry(self):
        """Get days until subscription expires"""
        from django.utils import timezone
        if self.subscription_end_date:
            delta = self.subscription_end_date - timezone.now()
            return max(0, delta.days)
        return 0
    
    def get_enabled_modules(self):
        """Get list of enabled modules for this hospital"""
        modules = []
        # Core modules (always enabled)
        modules.append('appointments')
        modules.append('patients')
        
        # Optional modules based on subscription
        if self.laboratory_enabled:
            modules.append('laboratory')
        if self.radiology_enabled:
            modules.append('radiology')
        if self.pharmacy_enabled:
            modules.append('pharmacy')
        if self.billing_enabled:
            modules.append('billing')
        if self.telemedicine_enabled:
            modules.append('telemedicine')
        if self.ipd_enabled:
            modules.append('ipd')
        if self.emergency_enabled:
            modules.append('emergency')
        return modules
    
    def get_user_count(self):
        """Get total number of users in this hospital"""
        return TenantAccess.objects.filter(tenant=self, is_active=True).count()
    
    def get_patient_count(self):
        """Get total number of patients in this hospital"""
        # This would integrate with your Patient model
        # For now, return a placeholder
        try:
            from apps.patients.models import Patient
            return Patient.objects.filter(hospital=self).count()
        except ImportError:
            return 0
    
    def get_appointment_count(self):
        """Get total number of appointments in this hospital"""
        try:
            from apps.appointments.models import Appointment
            return Appointment.objects.filter(hospital=self).count()
        except ImportError:
            return 0
    
    def get_active_user_count(self):
        """Get number of users who have accessed the system recently"""
        from django.utils import timezone
        from datetime import timedelta
        
        last_week = timezone.now() - timedelta(days=7)
        return TenantAccess.objects.filter(
            tenant=self, 
            is_active=True,
            last_accessed__gte=last_week
        ).count()
    
    def get_storage_usage(self):
        """Get storage usage in GB (placeholder implementation)"""
        # This would calculate actual file storage usage
        # For now, return a sample calculation
        return round(self.get_patient_count() * 0.5, 2)  # Assume 0.5GB per patient
    
    def get_plan_features(self):
        """Get features included in current subscription plan"""
        features = []
        
        if self.subscription_plan == 'BASIC':
            features = [
                'Up to 10 users',
                'Up to 500 patients',
                '10GB storage',
                'Basic appointments',
                'Patient records',
                'Email support'
            ]
        elif self.subscription_plan == 'STANDARD':
            features = [
                'Up to 25 users',
                'Up to 1,000 patients', 
                '50GB storage',
                'Advanced appointments',
                'Laboratory module',
                'Basic reporting',
                'Email & chat support'
            ]
        elif self.subscription_plan == 'PREMIUM':
            features = [
                'Up to 50 users',
                'Up to 2,500 patients',
                '100GB storage',
                'All basic modules',
                'Telemedicine',
                'Advanced reporting',
                'Priority support'
            ]
        elif self.subscription_plan == 'ENTERPRISE':
            features = [
                'Unlimited users',
                'Unlimited patients',
                '500GB storage',
                'All modules included',
                'Custom integrations',
                'Advanced analytics',
                'Dedicated support manager'
            ]
        
        return features

class TenantAccess(models.Model):
    """
    Track user access to different hospital tenants
    Each user can have access to multiple hospitals with different roles
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, help_text="Hospital this user has access to")
    role = models.CharField(max_length=50, default='STAFF', choices=[
        ('HOSPITAL_ADMIN', 'Hospital Administrator'),
        ('DOCTOR', 'Doctor'),
        ('NURSE', 'Nurse'),
        ('RECEPTIONIST', 'Receptionist'),
        ('PHARMACIST', 'Pharmacist'),
        ('LAB_TECHNICIAN', 'Lab Technician'),
        ('RADIOLOGIST', 'Radiologist'),
        ('ACCOUNTANT', 'Accountant'),
        ('STAFF', 'General Staff'),
    ])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_accessed = models.DateTimeField(auto_now=True)
    access_count = models.IntegerField(default=0, help_text="Number of times user has accessed this hospital")
    
    class Meta:
        db_table = 'tenants_tenant_access'
        verbose_name = 'Hospital Access'
        verbose_name_plural = 'Hospital Access Records'
        unique_together = ('user', 'tenant')  # User can have only one role per hospital
    
    def __str__(self):
        return f"{self.user.username} - {self.tenant.name} ({self.get_role_display()})"
