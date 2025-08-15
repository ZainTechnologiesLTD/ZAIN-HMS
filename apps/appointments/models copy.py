# appointments/models.py
from django.db import models
from patients.models import Patient
from doctors.models import Doctor, DoctorSchedule
from django.core.exceptions import ValidationError
from django.conf import settings
from django.utils.timezone import now
from pharmacy.models import Medicine
from django.utils import timezone

class Appointment(models.Model):
    APPOINTMENT_TYPES = [
        ('GENERAL', 'General'),
        ('OPD', 'Outpatient Department'),
        ('EMERGENCY', 'Emergency'),
        ('FOLLOW_UP', 'Follow-up'),
    ]
    APPOINTMENT_STATUS = [
        ('SCHEDULED', 'Scheduled'),
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED', 'Cancelled'),
        ('COMPLETED', 'Completed'),
    ]
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='appointments')
    appointment_type = models.CharField(max_length=20, choices=APPOINTMENT_TYPES, default="OPD")
    date_time = models.DateTimeField(default=now)
    status = models.CharField(max_length=20, choices=APPOINTMENT_STATUS, default='SCHEDULED')
    reason = models.TextField()
    fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_appointments')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    pass

    class Meta:
        # Existing Meta options...
        permissions = [
            ('cancel_appointment', 'Can cancel appointment'),
        ]

    def __str__(self):
        return f"Appointment for {self.patient} with Dr. {self.doctor.last_name} on {self.date_time}"
    
    class Meta:
        ordering = ['date_time']
        indexes = [
            models.Index(fields=['status']),
        ]



    def check_doctor_availability(self):
        if not hasattr(self, 'doctor') or not self.doctor:
            return True  # Skip availability check if doctor isn't set yet
            
        existing_appointments = Appointment.objects.filter(
            doctor=self.doctor,
            date_time=self.date_time,
            status='SCHEDULED'
        ).exclude(pk=self.pk)
        return not existing_appointments.exists()

    def clean(self):
        if hasattr(self, 'doctor') and self.doctor:
            if not self.check_doctor_availability():
                raise ValidationError('Doctor is not available at this time slot.')
# Move these models to appointments/models.py
class Prescription(models.Model):
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='prescriptions')
    date_time = models.DateTimeField(null=True, blank=True, default=timezone.now)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Prescription for appointment on {self.date_time}"

    class Meta:
        ordering = ['date_time']
        unique_together = ('appointment', 'date_time')

class PrescriptionMedicine(models.Model):
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name='prescription_medicines')
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, related_name='prescription_medicines')
    dosage = models.CharField(max_length=255)
    frequency = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.medicine.name} - Dosage: {self.dosage}, Frequency: {self.frequency}"    