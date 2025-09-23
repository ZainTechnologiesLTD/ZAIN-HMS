# apps/staff/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import RegexValidator
# # from apps.accounts.models import CustomUser as User

class Department(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
import uuid


class StaffProfile(models.Model):
    """
    Extended profile for staff members (non-doctor roles)
    Links to User model for authentication and basic info
    """
    
    EMPLOYMENT_TYPE_CHOICES = [
        ('FULL_TIME', 'Full Time'),
        ('PART_TIME', 'Part Time'),
        ('CONTRACT', 'Contract'),
        ('TEMPORARY', 'Temporary'),
        ('INTERN', 'Intern'),
    ]
    
    SHIFT_CHOICES = [
        ('MORNING', 'Morning Shift'),
        ('AFTERNOON', 'Afternoon Shift'),
        ('EVENING', 'Evening Shift'),
        ('NIGHT', 'Night Shift'),
        ('ROTATING', 'Rotating Shift'),
        ('FLEXIBLE', 'Flexible'),
    ]
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='staff_profile',
        null=True,
        blank=True
    )
    
    # Staff Details
    staff_id = models.CharField(max_length=20, unique=True, blank=True)
    generated_password = models.CharField(max_length=100, blank=True, help_text="Temporary storage for generated password")
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='staff_profiles')
    
    # Personal Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')])
    
    # Contact Information
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$')
    phone_number = models.CharField(validators=[phone_regex], max_length=17)
    email = models.EmailField(unique=True)
    address = models.TextField()
    emergency_contact_name = models.CharField(max_length=100)
    emergency_contact_phone = models.CharField(validators=[phone_regex], max_length=17)
    emergency_contact_relation = models.CharField(max_length=50)
    
    # Professional Information
    position_title = models.CharField(max_length=100)
    qualifications = models.TextField()
    certifications = models.TextField(blank=True)
    years_of_experience = models.PositiveIntegerField(default=0)
    specialization = models.CharField(max_length=100, blank=True)
    license_number = models.CharField(max_length=100, blank=True)
    
    # Employment Details
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPE_CHOICES, default='FULL_TIME')
    joining_date = models.DateField()
    probation_end_date = models.DateField(null=True, blank=True)
    contract_end_date = models.DateField(null=True, blank=True)
    shift = models.CharField(max_length=20, choices=SHIFT_CHOICES, default='MORNING')
    
    # Salary Information
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    hourly_rate = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_available = models.BooleanField(default=True)
    
    # Profile
    profile_picture = models.ImageField(upload_to='staff/profiles/', null=True, blank=True)
    bio = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='created_staff_profiles'
    )
    
    class Meta:
        ordering = ['first_name', 'last_name']
        verbose_name = 'Staff Profile'
        verbose_name_plural = 'Staff Profiles'
    
    def __str__(self):
        return f"{self.get_full_name()} - {self.position_title}"
    
    def save(self, *args, **kwargs):
        if not self.staff_id:
            self.staff_id = self.generate_staff_id()
        super().save(*args, **kwargs)
    
    def generate_staff_id(self):
        """Generate unique staff ID"""
        role_prefix = {
            'NURSE': 'NUR',
            'PHARMACIST': 'PHA',
            'LAB_TECHNICIAN': 'LAB',
            'RADIOLOGIST': 'RAD',
            'ACCOUNTANT': 'ACC',
            'HR_MANAGER': 'HRM',
            'RECEPTIONIST': 'REC',
            'STAFF': 'STF',
        }
        
        # Get role from user if linked, otherwise use STAFF
        role = self.user.role if self.user else 'STAFF'
        prefix = role_prefix.get(role, 'STF')
        
        year = timezone.now().year
        unique_suffix = str(uuid.uuid4())[:8].upper()
        return f"{prefix}-{year}-{unique_suffix}"
    
    def get_full_name(self):
        """Return the full name"""
        parts = [self.first_name, self.middle_name, self.last_name]
        return ' '.join(filter(None, parts))
    
    def get_display_name(self):
        """Return display name based on role"""
        if self.user and self.user.role == 'NURSE':
            return f"Nurse {self.get_full_name()}"
        elif self.user and self.user.role == 'RADIOLOGIST':
            return f"Dr. {self.get_full_name()}"
        return self.get_full_name()
    
    def get_role_display(self):
        """Get role display name"""
        if self.user:
            return self.user.get_role_display()
        return "Staff Member"


class StaffSchedule(models.Model):
    """Work schedule for staff members"""
    
    staff = models.ForeignKey(StaffProfile, on_delete=models.CASCADE, related_name='schedules')
    day_of_week = models.IntegerField(choices=[
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ])
    start_time = models.TimeField()
    end_time = models.TimeField()
    break_start_time = models.TimeField(null=True, blank=True)
    break_end_time = models.TimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['staff', 'day_of_week']
        ordering = ['day_of_week', 'start_time']
    
    def __str__(self):
        day_name = self.get_day_of_week_display()
        return f"{self.staff.get_full_name()} - {day_name} ({self.start_time} - {self.end_time})"


class StaffAttendance(models.Model):
    """Track staff attendance"""
    
    STATUS_CHOICES = [
        ('PRESENT', 'Present'),
        ('ABSENT', 'Absent'),
        ('LATE', 'Late'),
        ('HALF_DAY', 'Half Day'),
        ('SICK_LEAVE', 'Sick Leave'),
        ('CASUAL_LEAVE', 'Casual Leave'),
        ('EMERGENCY_LEAVE', 'Emergency Leave'),
    ]
    
    staff = models.ForeignKey(StaffProfile, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField()
    check_in_time = models.TimeField(null=True, blank=True)
    check_out_time = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PRESENT')
    working_hours = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    overtime_hours = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    marked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='marked_attendance'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['staff', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.staff.get_full_name()} - {self.date} ({self.status})"
