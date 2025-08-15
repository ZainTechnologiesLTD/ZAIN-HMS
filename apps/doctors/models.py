# doctors/models.py
from django.utils import timezone
import uuid
from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.models import User


class Doctor(models.Model):
    SPECIALIZATION_CHOICES = [
        ('CARDIOLOGY', 'Cardiology'),
        ('DERMATOLOGY', 'Dermatology'),
        ('NEUROLOGY', 'Neurology'),
        ('ORTHOPEDICS', 'Orthopedics')
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
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
        
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.specialization}"

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

    def is_available(self, date, time):
        if date.weekday() != self.day_of_week:
            return False
        if not (self.start_time <= time <= self.end_time):
            return False
        return not self.doctor.appointments.filter(date_time__date=date, date_time__time=time).exists()

    def __str__(self):
        return f"Dr. {self.doctor.last_name}, {self.doctor.first_name} ({self.doctor.specialization})"

