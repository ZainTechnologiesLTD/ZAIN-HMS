from django.db import models
from django.conf import settings
from apps.patients.models import Patient
from apps.doctors.models import Doctor


class TeleconsultationAppointment(models.Model):
    """Telemedicine video consultation appointments"""
    STATUS_CHOICES = [
        ('SCHEDULED', 'Scheduled'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('NO_SHOW', 'No Show'),
    ]
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    appointment_date = models.DateTimeField()
    duration_minutes = models.IntegerField(default=30)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCHEDULED')
    
    # Video call details
    meeting_room_id = models.CharField(max_length=100, unique=True)
    meeting_url = models.URLField(blank=True, null=True)
    
    # Consultation notes
    consultation_notes = models.TextField(blank=True)
    prescription = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'telemedicine_teleconsultation'
        verbose_name = 'Teleconsultation Appointment'
        verbose_name_plural = 'Teleconsultation Appointments'
    
    def __str__(self):
        return f"Teleconsultation: {self.patient.user.get_full_name()} with Dr. {self.doctor.user.get_full_name()}"


class VirtualWaitingRoom(models.Model):
    """Virtual waiting room for telemedicine"""
    appointment = models.OneToOneField(TeleconsultationAppointment, on_delete=models.CASCADE)
    patient_joined = models.BooleanField(default=False)
    doctor_joined = models.BooleanField(default=False)
    patient_join_time = models.DateTimeField(blank=True, null=True)
    doctor_join_time = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'telemedicine_virtual_waiting_room'
    
    def __str__(self):
        return f"Waiting Room: {self.appointment}"
