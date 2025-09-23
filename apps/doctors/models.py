# doctors/models.py
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import uuid
from django.db import models
from django.core.validators import RegexValidator
from django.conf import settings


class Doctor(models.Model):
    SPECIALIZATION_CHOICES = [
        ('ANESTHESIOLOGY', 'Anesthesiology'),
        ('CARDIOLOGY', 'Cardiology'),
        ('CARDIOTHORACIC_SURGERY', 'Cardiothoracic Surgery'),
        ('DERMATOLOGY', 'Dermatology'),
        ('EMERGENCY_MEDICINE', 'Emergency Medicine'),
        ('ENDOCRINOLOGY', 'Endocrinology'),
        ('FAMILY_MEDICINE', 'Family Medicine'),
        ('GASTROENTEROLOGY', 'Gastroenterology'),
        ('GENERAL_MEDICINE', 'General Medicine'),
        ('GENERAL_SURGERY', 'General Surgery'),
        ('GERIATRICS', 'Geriatrics'),
        ('GYNECOLOGY', 'Gynecology'),
        ('HEMATOLOGY', 'Hematology'),
        ('INFECTIOUS_DISEASE', 'Infectious Disease'),
        ('INTERNAL_MEDICINE', 'Internal Medicine'),
        ('NEPHROLOGY', 'Nephrology'),
        ('NEUROLOGY', 'Neurology'),
        ('NEUROSURGERY', 'Neurosurgery'),
        ('OBSTETRICS', 'Obstetrics'),
        ('ONCOLOGY', 'Oncology'),
        ('OPHTHALMOLOGY', 'Ophthalmology'),
        ('ORTHOPEDICS', 'Orthopedics'),
        ('OTOLARYNGOLOGY', 'Otolaryngology (ENT)'),
        ('PATHOLOGY', 'Pathology'),
        ('PEDIATRICS', 'Pediatrics'),
        ('PLASTIC_SURGERY', 'Plastic Surgery'),
        ('PSYCHIATRY', 'Psychiatry'),
        ('PULMONOLOGY', 'Pulmonology'),
        ('RADIOLOGY', 'Radiology'),
        ('RHEUMATOLOGY', 'Rheumatology'),
        ('UROLOGY', 'Urology'),
    ]
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    doctor_id = models.CharField(max_length=20, unique=True, blank=True, null=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    specialization = models.CharField(max_length=100, choices=SPECIALIZATION_CHOICES)
    license_number = models.CharField(max_length=50, unique=True)
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    phone_number = models.CharField(max_length=20)
    email = models.EmailField(unique=True)
    date_of_birth = models.DateField()
    address = models.TextField()
    image = models.ImageField(upload_to='photos/doctors', null=True, blank=True)
    joining_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.doctor_id:
            self.doctor_id = self.generate_unique_doctor_id()
        super(Doctor, self).save(*args, **kwargs)

    def generate_unique_doctor_id(self):
        prefix = "DR"
        year = timezone.now().year
        unique_suffix = str(uuid.uuid4())[:8]
        return f"{prefix}-{year}-{unique_suffix}"

    def generate_unique_username(self):
        return f"{self.first_name.lower()}.{self.last_name.lower()}.{uuid.uuid4().hex[:6]}"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
        
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.specialization}"
    
    class Meta:
        verbose_name = _('Doctor')
        verbose_name_plural = _('Doctors')

class DoctorSchedule(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='schedules')
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
    break_start_time = models.TimeField(null=True, blank=True, help_text="Break/lunch start time")
    break_end_time = models.TimeField(null=True, blank=True, help_text="Break/lunch end time")
    max_patients = models.PositiveIntegerField(default=20, help_text="Maximum patients for this time slot")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_available(self, date, time):
        if date.weekday() != self.day_of_week:
            return False
        if not (self.start_time <= time <= self.end_time):
            return False
        
        # Check if it's during break time
        if (self.break_start_time and self.break_end_time and 
            self.break_start_time <= time <= self.break_end_time):
            return False
            
        # Check if doctor is on leave
        if self.doctor.leaves.filter(start_date__lte=date, end_date__gte=date, is_approved=True).exists():
            return False
            
        return not self.doctor.appointments.filter(date_time__date=date, date_time__time=time).exists()

    def __str__(self):
        return f"Dr. {self.doctor.last_name}, {self.doctor.first_name} ({self.doctor.specialization})"
    
    class Meta:
        verbose_name = _('Doctor Schedule')
        verbose_name_plural = _('Doctor Schedules')


class DoctorLeave(models.Model):
    LEAVE_TYPE_CHOICES = [
        ('VACATION', 'Vacation'),
        ('SICK_LEAVE', 'Sick Leave'),
        ('CONFERENCE', 'Conference/Training'),
        ('EMERGENCY', 'Emergency Leave'),
        ('PERSONAL', 'Personal Leave'),
        ('MATERNITY', 'Maternity Leave'),
        ('PATERNITY', 'Paternity Leave'),
        ('BEREAVEMENT', 'Bereavement Leave'),
        ('OTHER', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='leaves')
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPE_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    contact_info = models.CharField(max_length=200, blank=True, null=True, help_text="Emergency contact during leave")
    covering_doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True, 
                                       related_name='covering_leaves', help_text="Doctor covering during this leave")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='approved_leaves')
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        # Update is_approved based on status
        self.is_approved = (self.status == 'APPROVED')
        if self.is_approved and not self.approved_at:
            self.approved_at = timezone.now()
        super().save(*args, **kwargs)
    
    def get_duration_days(self):
        """Calculate leave duration in days"""
        return (self.end_date - self.start_date).days + 1
    
    def is_current(self):
        """Check if leave is currently active"""
        today = timezone.now().date()
        return (self.start_date <= today <= self.end_date and 
                self.is_approved)
    
    def __str__(self):
        return f"Dr. {self.doctor.get_full_name()} - {self.get_leave_type_display()} ({self.start_date} to {self.end_date})"
    
    class Meta:
        verbose_name = _('Doctor Leave')
        verbose_name_plural = _('Doctor Leaves')
        ordering = ['-start_date']


class ScheduleTemplate(models.Model):
    """Pre-defined schedule templates for quick setup"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_default = models.BooleanField(default=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = _('Schedule Template')
        verbose_name_plural = _('Schedule Templates')


class ScheduleTemplateSlot(models.Model):
    """Individual time slots for schedule templates"""
    template = models.ForeignKey(ScheduleTemplate, on_delete=models.CASCADE, related_name='slots')
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
    max_patients = models.PositiveIntegerField(default=20)
    
    def __str__(self):
        return f"{self.template.name} - {self.get_day_of_week_display()} {self.start_time}-{self.end_time}"
    
    class Meta:
        verbose_name = _('Schedule Template Slot')
        verbose_name_plural = _('Schedule Template Slots')

