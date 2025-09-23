from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('SUPERADMIN', 'Super Administrator'),
        ('ADMIN', 'Hospital Administrator'),
        ('DOCTOR', 'Doctor'),
        ('NURSE', 'Nurse'),
        ('RECEPTIONIST', 'Receptionist'),
        ('PHARMACIST', 'Pharmacist'),
        ('LAB_TECHNICIAN', 'Lab Technician'),
        ('RADIOLOGIST', 'Radiologist'),
        ('ACCOUNTANT', 'Accountant'),
        ('PATIENT', 'Patient'),
        ('STAFF', 'General Staff'),
    ]
    
    is_superadmin = models.BooleanField(default=False)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='STAFF')
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=10, choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')], blank=True, null=True)
    emergency_contact = models.CharField(max_length=100, blank=True, null=True)
    employee_id = models.CharField(max_length=20, blank=True, null=True, unique=True)
    is_active_staff = models.BooleanField(default=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True, help_text="Profile picture")
    # UI Preferences
    theme_preference = models.CharField(max_length=20, blank=True, null=True, help_text="Preferred dashboard theme (dark, light, flat, teal, slate, neutral)")
    currency_preference = models.CharField(max_length=10, blank=True, null=True, help_text="Preferred currency code (ISO 4217, e.g., USD, EUR, INR)")

    def __str__(self):
        return f"{self.username} ({self.get_role_display()}) - ZAIN HMS"
    def has_module_permission(self, module_name):
        """Check if user has permission to access a module based on their role"""
        if self.is_superuser or self.role == 'SUPERADMIN':
            return True
        
        # ZAIN HMS unified system - no hospital-specific modules        
        module_permissions = {
            'patients': ['DOCTOR', 'NURSE', 'RECEPTIONIST'],
            'appointments': ['DOCTOR', 'NURSE', 'RECEPTIONIST', 'PATIENT'],
            'doctors': ['DOCTOR', 'NURSE'],
            'nurses': ['DOCTOR', 'NURSE'],
            'billing': ['ACCOUNTANT', 'RECEPTIONIST', 'PATIENT'],
            'pharmacy': ['PHARMACIST', 'DOCTOR'],
            'laboratory': ['LAB_TECHNICIAN', 'DOCTOR', 'PATIENT'],
            'radiology': ['RADIOLOGIST', 'DOCTOR', 'PATIENT'],
            'telemedicine': ['DOCTOR', 'NURSE', 'PATIENT'],
            'emergency': ['DOCTOR', 'NURSE'],
            'inventory': ['PHARMACIST'],
            'reports': ['ACCOUNTANT', 'DOCTOR'],
            'analytics': ['ACCOUNTANT', 'DOCTOR'],
            'surgery': ['DOCTOR'],
            'ipd': ['DOCTOR', 'NURSE'],
            'opd': ['DOCTOR', 'NURSE', 'RECEPTIONIST'],
            'staff': [],  # Only admin access via Django admin
            'notifications': ['DOCTOR', 'NURSE', 'RECEPTIONIST', 'PATIENT'],
            'dashboard': ['DOCTOR', 'NURSE', 'RECEPTIONIST', 'PATIENT'],
            'emr': ['DOCTOR', 'NURSE', 'PATIENT'],
            'room_management': ['NURSE'],
            'communications': ['DOCTOR', 'NURSE', 'RECEPTIONIST', 'PATIENT'],
        }
        
        allowed_roles = module_permissions.get(module_name, [])
        return self.role in allowed_roles
    
    def has_module_perms(self, app_label):
        """
        Django Admin Access Control - Only SUPERADMIN can access Django admin
        Hospital ADMIN users should use the frontend interface only
        """
        if not self.is_active:
            return False
        
        # Only SUPERADMIN users can access Django admin
        if self.role == 'SUPERADMIN' or self.is_superuser:
            return True
            
        return False
    
    def has_perm(self, perm, obj=None):
        """
        Django Admin Permission Control - Only SUPERADMIN has Django admin permissions
        """
        if not self.is_active:
            return False
            
        # Only SUPERADMIN users have Django admin permissions
        if self.role == 'SUPERADMIN' or self.is_superuser:
            return True
            
            return False
        
    def save(self, *args, **kwargs):
        """Override save to handle ZAIN HMS user role permissions"""
        # SECURITY: Enforce strict admin-site access rules
        if self.is_superuser or self.role == 'SUPERADMIN':
            # Only SUPERADMIN role can have Django admin access
            self.role = 'SUPERADMIN'
            self.is_staff = True  # Allow Django admin access
            self.is_superuser = True
        else:
            # SECURITY: Force all non-SUPERADMIN users to NOT have Django admin access
            # This prevents privilege escalation attacks
            self.is_superuser = False
            self.is_staff = False  # Block Django admin access

        # Simple save for ZAIN HMS unified system
        super().save(*args, **kwargs)
