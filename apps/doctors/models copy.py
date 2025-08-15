# apps/doctors/models.py
from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
from apps.accounts.models import Hospital, User, Department
import uuid

class Doctor(models.Model):
    """Doctor model with complete professional information"""
    
    SPECIALIZATION_CHOICES = [
        ('GENERAL', 'General Medicine'),
        ('CARDIOLOGY', 'Cardiology'),
        ('DERMATOLOGY', 'Dermatology'),
        ('ENDOCRINOLOGY', 'Endocrinology'),
        ('GASTROENTEROLOGY', 'Gastroenterology'),
        ('NEUROLOGY', 'Neurology'),
        ('ONCOLOGY', 'Oncology'),
        ('ORTHOPEDICS', 'Orthopedics'),
        ('PEDIATRICS', 'Pediatrics'),
        ('PSYCHIATRY', 'Psychiatry'),
        ('RADIOLOGY', 'Radiology'),
        ('SURGERY', 'Surgery'),
        ('UROLOGY', 'Urology'),
        ('GYNECOLOGY', 'Gynecology'),
        ('OPHTHALMOLOGY', 'Ophthalmology'),
        ('ENT', 'ENT (Ear, Nose, Throat)'),
        ('ANESTHESIOLOGY', 'Anesthesiology'),
        ('PATHOLOGY', 'Pathology'),
        ('EMERGENCY', 'Emergency Medicine'),
    ]
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='doctors')
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile')
    doctor_id = models.CharField(max_length=20, unique=True, blank=True)
    
    # Professional Information
    specialization = models.CharField(max_length=50, choices=SPECIALIZATION_CHOICES)
    sub_specialization = models.CharField(max_length=100, blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Qualifications and Experience
    medical_degree = models.CharField(max_length=200)
    additional_qualifications = models.TextField(blank=True)
    medical_license_number = models.CharField(max_length=100, unique=True)
    license_expiry_date = models.DateField()
    years_of_experience = models.PositiveIntegerField(default=0)
    
    # Contact Information
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$')
    professional_phone = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    professional_email = models.EmailField(blank=True)
    
    # Consultation Information
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    follow_up_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    average_consultation_time = models.PositiveIntegerField(default=30, help_text="Minutes")
    
    # Professional Details
    biography = models.TextField(blank=True)
    languages_spoken = models.CharField(max_length=200, blank=True, help_text="Comma-separated languages")
    
    # Hospital Information
    room_number = models.CharField(max_length=20, blank=True)
    extension_number = models.CharField(max_length=10, blank=True)
    
    # Availability
    is_available = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    
    # Ratings and Reviews
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_reviews = models.PositiveIntegerField(default=0)
    
    # Professional Image
    professional_photo = models.ImageField(upload_to='doctors/photos/', null=True, blank=True)
    
    # Timestamps
    joined_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['user__last_name', 'user__first_name']
        indexes = [
            models.Index(fields=['doctor_id']),
            models.Index(fields=['specialization']),
            models.Index(fields=['is_active', 'is_available']),
        ]
    
    def __str__(self):
        return f"Dr. {self.user.get_full_name()} ({self.get_specialization_display()})"
    
    def save(self, *args, **kwargs):
        if not self.doctor_id:
            self.doctor_id = self.generate_doctor_id()
        super().save(*args, **kwargs)
    
    def generate_doctor_id(self):
        """Generate unique doctor ID"""
        last_doctor = Doctor.objects.filter(
            hospital=self.hospital
        ).order_by('-created_at').first()
        
        if last_doctor and last_doctor.doctor_id:
            try:
                last_number = int(last_doctor.doctor_id.split('-')[-1])
                new_number = last_number + 1
            except:
                new_number = 1
        else:
            new_number = 1
            
        return f"{self.hospital.code}-DOC-{new_number:05d}"
    
    def get_full_name(self):
        """Return full name with title"""
        return f"Dr. {self.user.get_full_name()}"
    
    def get_languages_list(self):
        """Return list of languages"""
        if self.languages_spoken:
            return [lang.strip() for lang in self.languages_spoken.split(',')]
        return []
    
    def get_total_patients(self):
        """Get total number of unique patients"""
        return self.appointments.values('patient').distinct().count()
    
    def get_today_appointments(self):
        """Get today's appointments"""
        today = timezone.now().date()
        return self.appointments.filter(
            appointment_date=today,
            status__in=['SCHEDULED', 'CONFIRMED', 'CHECKED_IN', 'IN_PROGRESS']
        )


class DoctorSchedule(models.Model):
    """Doctor's working schedule"""
    DAYS_OF_WEEK = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]
    
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='schedules')
    day_of_week = models.PositiveIntegerField(choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()
    break_start_time = models.TimeField(null=True, blank=True)
    break_end_time = models.TimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['doctor', 'day_of_week']
        ordering = ['day_of_week', 'start_time']
    
    def __str__(self):
        return f"{self.doctor.get_full_name()} - {self.get_day_of_week_display()}"
    
    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError("End time must be after start time")
        
        if self.break_start_time and self.break_end_time:
            if self.break_start_time >= self.break_end_time:
                raise ValidationError("Break end time must be after break start time")
            if not (self.start_time <= self.break_start_time < self.break_end_time <= self.end_time):
                raise ValidationError("Break time must be within working hours")


class DoctorLeave(models.Model):
    """Doctor's leave and unavailability"""
    LEAVE_TYPES = [
        ('VACATION', 'Vacation'),
        ('SICK', 'Sick Leave'),
        ('CONFERENCE', 'Conference'),
        ('EMERGENCY', 'Emergency'),
        ('PERSONAL', 'Personal'),
        ('OTHER', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='leaves')
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # Approval Information
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_doctor_leaves')
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    
    # Timestamps
    requested_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.doctor.get_full_name()} - {self.get_leave_type_display()} ({self.start_date} to {self.end_date})"
    
    def clean(self):
        if self.start_date > self.end_date:
            raise ValidationError("End date must be after start date")


class DoctorReview(models.Model):
    """Patient reviews for doctors"""
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='reviews')
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='doctor_reviews')
    appointment = models.OneToOneField('appointments.Appointment', on_delete=models.CASCADE, null=True, blank=True)
    
    rating = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)])  # 1-5 stars
    review_text = models.TextField(blank=True)
    
    # Review categories
    bedside_manner_rating = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)], null=True, blank=True)
    punctuality_rating = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)], null=True, blank=True)
    expertise_rating = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)], null=True, blank=True)
    
    is_approved = models.BooleanField(default=False)
    is_anonymous = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['doctor', 'patient', 'appointment']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Review for {self.doctor.get_full_name()} by {self.patient.get_full_name()}"