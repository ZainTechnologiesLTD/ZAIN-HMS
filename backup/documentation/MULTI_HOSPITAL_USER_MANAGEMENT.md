# Multi-Hospital User Management Enhancement

# apps/accounts/models.py - Add this new model

class UserHospitalAffiliation(models.Model):
    """
    Many-to-Many relationship between Users and Hospitals
    Allows doctors, nurses, and staff to work at multiple hospitals
    """
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='hospital_affiliations')
    hospital = models.ForeignKey('Hospital', on_delete=models.CASCADE, related_name='affiliated_users')
    
    # Affiliation details
    role_at_hospital = models.CharField(
        max_length=20, 
        choices=User.ROLE_CHOICES,
        help_text="User's specific role at this hospital"
    )
    department = models.ForeignKey(
        'Department', 
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        help_text="Department at this specific hospital"
    )
    
    # Status and permissions
    is_primary = models.BooleanField(
        default=False,
        help_text="Is this the user's primary hospital?"
    )
    is_active = models.BooleanField(default=True)
    can_access_billing = models.BooleanField(default=False)
    can_access_pharmacy = models.BooleanField(default=False)
    can_access_lab = models.BooleanField(default=False)
    can_access_radiology = models.BooleanField(default=False)
    
    # Employment details
    employee_id_at_hospital = models.CharField(
        max_length=50, 
        blank=True,
        help_text="Employee ID specific to this hospital"
    )
    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField(null=True, blank=True)
    
    # Schedule and availability
    working_days = models.JSONField(
        default=list,
        help_text="List of working days: ['Monday', 'Tuesday', ...]"
    )
    working_hours = models.JSONField(
        default=dict,
        help_text="Working hours: {'start': '09:00', 'end': '17:00'}"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'User', 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='created_affiliations'
    )
    
    class Meta:
        unique_together = ['user', 'hospital']
        ordering = ['-is_primary', 'hospital__name']
        verbose_name = "User Hospital Affiliation"
        verbose_name_plural = "User Hospital Affiliations"
    
    def __str__(self):
        primary = " (Primary)" if self.is_primary else ""
        return f"{self.user.get_full_name()} - {self.hospital.name}{primary}"
    
    def save(self, *args, **kwargs):
        # Ensure only one primary hospital per user
        if self.is_primary:
            UserHospitalAffiliation.objects.filter(
                user=self.user, 
                is_primary=True
            ).exclude(
                id=self.id
            ).update(is_primary=False)
        
        super().save(*args, **kwargs)


# Enhanced User Model Methods (add to existing User model)

class User(AbstractUser):
    # ... existing fields ...
    
    def get_hospitals(self):
        """Get all hospitals this user is affiliated with"""
        return Hospital.objects.filter(
            affiliated_users__user=self,
            affiliated_users__is_active=True
        ).distinct()
    
    def get_primary_hospital(self):
        """Get user's primary hospital"""
        try:
            affiliation = self.hospital_affiliations.filter(
                is_primary=True, 
                is_active=True
            ).first()
            return affiliation.hospital if affiliation else self.hospital
        except:
            return self.hospital
    
    def get_hospital_role(self, hospital):
        """Get user's role at a specific hospital"""
        try:
            affiliation = self.hospital_affiliations.get(
                hospital=hospital,
                is_active=True
            )
            return affiliation.role_at_hospital
        except UserHospitalAffiliation.DoesNotExist:
            return self.role
    
    def can_access_hospital(self, hospital):
        """Check if user can access a specific hospital"""
        if self.role == 'SUPERADMIN':
            return True
        
        if self.hospital == hospital:
            return True
            
        return self.hospital_affiliations.filter(
            hospital=hospital,
            is_active=True
        ).exists()
    
    def has_multiple_hospitals(self):
        """Check if user works at multiple hospitals"""
        return self.get_hospitals().count() > 1
