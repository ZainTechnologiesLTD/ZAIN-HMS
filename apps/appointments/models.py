# apps/appointments/models.py
from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
from django.core.exceptions import ValidationError
from apps.accounts.models import Hospital, User
from apps.patients.models import Patient
from apps.doctors.models import Doctor
import uuid

class AppointmentType(models.Model):
    """Different types of appointments"""
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='appointment_types')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    duration_minutes = models.PositiveIntegerField(default=30)
    color = models.CharField(max_length=7, default='#007bff', help_text="Color for calendar display")
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['hospital', 'name']
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Appointment(models.Model):
    """Appointment model with comprehensive scheduling"""
    
    STATUS_CHOICES = [
        ('SCHEDULED', 'Scheduled'),
        ('CONFIRMED', 'Confirmed'),
        ('CHECKED_IN', 'Checked In'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('NO_SHOW', 'No Show'),
        ('RESCHEDULED', 'Rescheduled'),
    ]
    
    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('NORMAL', 'Normal'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ]
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='appointments')
    appointment_number = models.CharField(max_length=20, unique=True, blank=True)
    
    # Participants
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='appointments')
    
    # Appointment Details
    appointment_type = models.ForeignKey(AppointmentType, on_delete=models.SET_NULL, null=True)
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    duration_minutes = models.PositiveIntegerField(default=30)
    
    # Status and Priority
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCHEDULED')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='NORMAL')
    
    # Medical Information
    chief_complaint = models.TextField(help_text="Primary reason for visit")
    symptoms = models.TextField(blank=True, help_text="Patient reported symptoms")
    notes = models.TextField(blank=True, help_text="Additional notes")
    
    # Follow-up
    is_follow_up = models.BooleanField(default=False)
    previous_appointment = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='follow_ups')
    
    # Financial
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_paid = models.BooleanField(default=False)
    payment_method = models.CharField(max_length=20, blank=True)
    
    # Tracking
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_appointments')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Check-in Information
    checked_in_at = models.DateTimeField(null=True, blank=True)
    checked_in_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='checked_in_appointments')
    
    # Completion Information
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Cancellation Information
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancelled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='cancelled_appointments')
    cancellation_reason = models.TextField(blank=True)
    
    class Meta:
        ordering = ['appointment_date', 'appointment_time']
        indexes = [
            models.Index(fields=['appointment_date', 'appointment_time']),
            models.Index(fields=['status']),
            models.Index(fields=['patient']),
            models.Index(fields=['doctor']),
        ]
    
    def __str__(self):
        return f"{self.patient.get_full_name()} with {self.doctor.get_full_name()} on {self.appointment_date} at {self.appointment_time}"
    
    def save(self, *args, **kwargs):
        if not self.appointment_number:
            self.appointment_number = self.generate_appointment_number()
        super().save(*args, **kwargs)
    
    def generate_appointment_number(self):
        """Generate unique appointment number"""
        from datetime import datetime
        
        last_appointment = Appointment.objects.filter(
            hospital=self.hospital,
            created_at__date=datetime.now().date()
        ).order_by('-created_at').first()
        
        if last_appointment and last_appointment.appointment_number:
            try:
                last_number = int(last_appointment.appointment_number.split('-')[-1])
                new_number = last_number + 1
            except:
                new_number = 1
        else:
            new_number = 1
            
        date_str = datetime.now().strftime('%Y%m%d')
        return f"{self.hospital.code}-APT-{date_str}-{new_number:04d}"
    
    def clean(self):
        # Check if appointment time is in the future
        if self.appointment_date and self.appointment_time:
            appointment_datetime = timezone.make_aware(
                timezone.datetime.combine(self.appointment_date, self.appointment_time)
            )
            if appointment_datetime <= timezone.now():
                raise ValidationError("Appointment must be scheduled for a future date and time.")
        
        # Check for conflicting appointments
        if self.doctor and self.appointment_date and self.appointment_time:
            conflicting_appointments = Appointment.objects.filter(
                doctor=self.doctor,
                appointment_date=self.appointment_date,
                appointment_time=self.appointment_time,
                status__in=['SCHEDULED', 'CONFIRMED', 'CHECKED_IN', 'IN_PROGRESS']
            ).exclude(pk=self.pk)
            
            if conflicting_appointments.exists():
                raise ValidationError("Doctor is not available at this time.")
    
    def get_datetime(self):
        """Return combined datetime object"""
        return timezone.make_aware(
            timezone.datetime.combine(self.appointment_date, self.appointment_time)
        )
    
    def get_end_datetime(self):
        """Return appointment end datetime"""
        start_datetime = self.get_datetime()
        return start_datetime + timezone.timedelta(minutes=self.duration_minutes)
    
    def can_be_cancelled(self):
        """Check if appointment can be cancelled"""
        return self.status in ['SCHEDULED', 'CONFIRMED']
    
    def can_be_rescheduled(self):
        """Check if appointment can be rescheduled"""
        return self.status in ['SCHEDULED', 'CONFIRMED']
    
    def get_status_color(self):
        """Return Bootstrap color class for status"""
        colors = {
            'SCHEDULED': 'primary',
            'CONFIRMED': 'info',
            'CHECKED_IN': 'warning',
            'IN_PROGRESS': 'warning',
            'COMPLETED': 'success',
            'CANCELLED': 'danger',
            'NO_SHOW': 'secondary',
            'RESCHEDULED': 'info',
        }
        return colors.get(self.status, 'secondary')


class AppointmentHistory(models.Model):
    """Track appointment status changes"""
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='history')
    old_status = models.CharField(max_length=20, choices=Appointment.STATUS_CHOICES)
    new_status = models.CharField(max_length=20, choices=Appointment.STATUS_CHOICES)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)
    reason = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-changed_at']
        verbose_name_plural = "Appointment Histories"
    
    def __str__(self):
        return f"{self.appointment.appointment_number}: {self.old_status} → {self.new_status}"


class AppointmentReminder(models.Model):
    """Appointment reminders and notifications"""
    REMINDER_TYPES = [
        ('EMAIL', 'Email'),
        ('SMS', 'SMS'),
        ('WHATSAPP', 'WhatsApp'),
        ('PUSH', 'Push Notification'),
    ]
    
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='reminders')
    reminder_type = models.CharField(max_length=20, choices=REMINDER_TYPES)
    scheduled_at = models.DateTimeField()
    sent_at = models.DateTimeField(null=True, blank=True)
    is_sent = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)
    
    class Meta:
        ordering = ['scheduled_at']
    
    def __str__(self):
        return f"{self.reminder_type} reminder for {self.appointment.appointment_number}"