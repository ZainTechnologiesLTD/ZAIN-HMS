from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from doctors.models import Doctor
from django.contrib.auth.models import User

class EmergencyCase(models.Model):
    PRIORITY_CHOICES = [
        ('critical', _('Critical')),
        ('high', _('High')),
        ('medium', _('Medium')),
        ('low', _('Low')),
    ]

    STATUS_CHOICES = [
        ('waiting', _('Waiting')),
        ('in_treatment', _('In Treatment')),
        ('stabilized', _('Stabilized')),
        ('transferred', _('Transferred')),
        ('discharged', _('Discharged')),
    ]

    case_number = models.CharField(max_length=20, unique=True)
    patient_name = models.CharField(max_length=255)
    age = models.IntegerField()
    contact_number = models.CharField(max_length=20)
    arrival_time = models.DateTimeField(default=timezone.now)
    chief_complaint = models.TextField()
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting')
    assigned_doctor = models.ForeignKey(
        Doctor,
        on_delete=models.SET_NULL,
        null=True,
        related_name='emergency_cases'
    )
    vital_signs = models.JSONField(default=dict)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-arrival_time']
        verbose_name = _('Emergency Case')
        verbose_name_plural = _('Emergency Cases')

    def __str__(self):
        return f"{self.case_number} - {self.patient_name}"

    def save(self, *args, **kwargs):
        if not self.case_number:
            last_case = EmergencyCase.objects.order_by('-id').first()
            if last_case:
                last_number = int(last_case.case_number[2:])
                self.case_number = f'EC{str(last_number + 1).zfill(6)}'
            else:
                self.case_number = 'EC000001'
        super().save(*args, **kwargs)

class EmergencyTreatment(models.Model):
    case = models.ForeignKey(
        EmergencyCase,
        on_delete=models.CASCADE,
        related_name='treatments'
    )
    treatment_time = models.DateTimeField(default=timezone.now)
    procedure = models.TextField()
    medications = models.JSONField(default=list)
    performed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='emergency_treatments'
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-treatment_time']
        verbose_name = _('Emergency Treatment')
        verbose_name_plural = _('Emergency Treatments')