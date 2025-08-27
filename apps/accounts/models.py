from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('SUPERADMIN', 'Super Administrator'),
        ('HOSPITAL_ADMIN', 'Hospital Administrator'), 
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
    
    # Direct hospital relationship - One user belongs to ONE hospital only
    hospital = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, null=True, blank=True, 
                                related_name='users', help_text="Hospital this user belongs to")

    def __str__(self):
        hospital_name = self.hospital.name if self.hospital else "No Hospital"
        return f"{self.username} ({self.get_role_display()}) - {hospital_name}"
    
    def get_current_hospital(self):
        """Get user's hospital"""
        return self.hospital
    
    def has_hospital_access(self, hospital_id):
        """Check if user has access to specific hospital - simplified for single hospital"""
        return self.hospital and self.hospital.id == hospital_id
    
    def get_role_in_hospital(self, hospital=None):
        """Get user's role - simplified since user belongs to one hospital"""
        return self.role
    
    def has_module_permission(self, module_name):
        """Check if user has permission to access a module based on their role"""
        if self.is_superuser or self.role == 'SUPERADMIN':
            return True
        
        if not self.hospital:
            return False
            
        if self.role == 'HOSPITAL_ADMIN':
            return True
            
        module_permissions = {
            'patients': ['DOCTOR', 'NURSE', 'RECEPTIONIST'],
            'appointments': ['DOCTOR', 'NURSE', 'RECEPTIONIST'],
            'doctors': ['HOSPITAL_ADMIN', 'DOCTOR', 'NURSE'],
            'nurses': ['HOSPITAL_ADMIN', 'DOCTOR', 'NURSE'],
            'billing': ['ACCOUNTANT', 'RECEPTIONIST', 'HOSPITAL_ADMIN'],
            'pharmacy': ['PHARMACIST', 'DOCTOR'],
            'laboratory': ['LAB_TECHNICIAN', 'DOCTOR'],
            'radiology': ['RADIOLOGIST', 'DOCTOR'],
            'telemedicine': ['DOCTOR', 'NURSE', 'HOSPITAL_ADMIN'],
            'emergency': ['DOCTOR', 'NURSE'],
            'inventory': ['PHARMACIST', 'HOSPITAL_ADMIN'],
            'reports': ['HOSPITAL_ADMIN', 'ACCOUNTANT', 'DOCTOR'],
            'analytics': ['HOSPITAL_ADMIN', 'ACCOUNTANT', 'DOCTOR'],
            'surgery': ['DOCTOR'],
            'ipd': ['DOCTOR', 'NURSE'],
            'opd': ['DOCTOR', 'NURSE', 'RECEPTIONIST'],
            'staff': ['HOSPITAL_ADMIN'],
            'notifications': ['HOSPITAL_ADMIN', 'DOCTOR', 'NURSE', 'RECEPTIONIST'],
        }
        
        allowed_roles = module_permissions.get(module_name, [])
        return self.role in allowed_roles
        
    def save(self, *args, **kwargs):
        """Override save to ensure username uniqueness within hospital context"""
        # Enforce admin-site access rules: only SUPERADMIN role should have
        # is_staff/is_superuser flags. Hospital admins must authenticate via
        # the public/user login UI (not Django admin).
        if self.role == 'SUPERADMIN':
            self.is_staff = True
            self.is_superuser = True
        else:
            # Ensure other roles are not granted Django admin access by mistake
            self.is_staff = False
            # Keep is_superuser only if explicitly set by system admin; by
            # default revoke it for non-superadmins
            self.is_superuser = False

        if self.hospital and self.pk is None:  # New user creation
            # Check if username already exists for this hospital or globally
            if CustomUser.objects.filter(username=self.username).exists():
                from django.core.exceptions import ValidationError
                raise ValidationError(f"Username '{self.username}' is already taken. Please choose a different username.")

        super().save(*args, **kwargs)
