# apps/accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator
import uuid

class Hospital(models.Model):
    """Multi-tenant Hospital Model"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    logo = models.ImageField(upload_to='hospitals/logos/', null=True, blank=True)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$')
    phone = models.CharField(validators=[phone_regex], max_length=17)
    email = models.EmailField()
    website = models.URLField(blank=True, null=True)
    
    # Subscription Information
    subscription_plan = models.CharField(
        max_length=20,
        choices=[
            ('TRIAL', 'Trial'),
            ('BASIC', 'Basic'),
            ('PROFESSIONAL', 'Professional'),
            ('ENTERPRISE', 'Enterprise'),
        ],
        default='TRIAL'
    )
    subscription_status = models.CharField(
        max_length=20,
        choices=[
            ('ACTIVE', 'Active'),
            ('EXPIRED', 'Expired'),
            ('SUSPENDED', 'Suspended'),
        ],
        default='ACTIVE'
    )
    subscription_start = models.DateField(auto_now_add=True)
    subscription_end = models.DateField(null=True, blank=True)
    
    # Settings
    settings = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        
    def __str__(self):
        return self.name
    
    def is_subscription_active(self):
        if self.subscription_status != 'ACTIVE':
            return False
        if self.subscription_end and self.subscription_end < timezone.now().date():
            return False
        return True


class Department(models.Model):
    """Hospital Departments"""
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='departments')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)
    description = models.TextField(blank=True)
    head = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True, related_name='headed_departments')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['hospital', 'code']
        ordering = ['name']
        
    def __str__(self):
        return f"{self.name} - {self.hospital.name}"


class User(AbstractUser):
    """Custom User Model with Role-Based Access"""
    ROLE_CHOICES = [
        ('SUPERADMIN', 'Super Administrator'),
        ('ADMIN', 'Hospital Administrator'),
        ('DOCTOR', 'Doctor'),
        ('NURSE', 'Nurse'),
        ('RECEPTIONIST', 'Receptionist'),
        ('PHARMACIST', 'Pharmacist'),
        ('LAB_TECHNICIAN', 'Laboratory Technician'),
        ('RADIOLOGIST', 'Radiologist'),
        ('ACCOUNTANT', 'Accountant'),
        ('HR_MANAGER', 'HR Manager'),
        ('PATIENT', 'Patient'),
        ('STAFF', 'Staff'),
    ]
    
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    BLOOD_GROUP_CHOICES = [
        ('A+', 'A Positive'),
        ('A-', 'A Negative'),
        ('B+', 'B Positive'),
        ('B-', 'B Negative'),
        ('AB+', 'AB Positive'),
        ('AB-', 'AB Negative'),
        ('O+', 'O Positive'),
        ('O-', 'O Negative'),
    ]
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, null=True, blank=True, related_name='users')
    employee_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='PATIENT')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    
    # Personal Information
    middle_name = models.CharField(max_length=50, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True, blank=True)
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES, null=True, blank=True)
    
    # Contact Information
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$')
    phone = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    alternate_phone = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    
    # Professional Information
    specialization = models.CharField(max_length=100, blank=True)
    qualification = models.TextField(blank=True)
    experience_years = models.PositiveIntegerField(default=0)
    license_number = models.CharField(max_length=100, blank=True)
    joining_date = models.DateField(null=True, blank=True)
    
    # Emergency Contact
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    emergency_contact_relation = models.CharField(max_length=50, blank=True)
    
    # Profile
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    bio = models.TextField(blank=True)
    
    # Status
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_users')
    approved_at = models.DateTimeField(null=True, blank=True)
    is_available = models.BooleanField(default=True)
    last_activity = models.DateTimeField(null=True, blank=True)
    
    # Settings
    preferences = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['first_name', 'last_name']
        
    def __str__(self):
        return self.get_full_name() or self.username
    
    def get_full_name(self):
        """Return the full name of the user"""
        parts = [self.first_name, self.middle_name, self.last_name]
        return ' '.join(filter(None, parts))
    
    def get_display_name(self):
        """Return display name based on role"""
        if self.role == 'DOCTOR':
            return f"Dr. {self.get_full_name()}"
        return self.get_full_name()
    
    def has_module_permission(self, module_name):
        """Check if user has permission to access a module"""
        if self.is_superuser or self.role == 'SUPERADMIN':
            return True
            
        if self.role == 'ADMIN':
            return True
            
        module_permissions = {
            'patients': ['DOCTOR', 'NURSE', 'RECEPTIONIST'],
            'appointments': ['DOCTOR', 'NURSE', 'RECEPTIONIST'],
            'billing': ['ACCOUNTANT', 'RECEPTIONIST', 'ADMIN'],
            'pharmacy': ['PHARMACIST', 'DOCTOR'],
            'laboratory': ['LAB_TECHNICIAN', 'DOCTOR'],
            'emergency': ['DOCTOR', 'NURSE'],
            'inventory': ['PHARMACIST', 'ADMIN'],
            'reports': ['ADMIN', 'ACCOUNTANT', 'DOCTOR'],
        }
        
        allowed_roles = module_permissions.get(module_name, [])
        return self.role in allowed_roles


class UserSession(models.Model):
    """Track user sessions for security"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(max_length=40, unique=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-last_activity']