from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


class EmergencyCase(models.Model):
    """Emergency case model with status and priority fields."""
    
    STATUS_CHOICES = [
        ('waiting', 'Waiting'),
        ('in_treatment', 'In Treatment'),
        ('observation', 'Under Observation'),
        ('discharged', 'Discharged'),
        ('transferred', 'Transferred'),
    ]
    
    PRIORITY_CHOICES = [
        ('critical', 'Critical'),
        ('urgent', 'Urgent'),
        ('semi_urgent', 'Semi-Urgent'),
        ('non_urgent', 'Non-Urgent'),
    ]
    
    case_number = models.CharField(max_length=100, unique=True)
    patient_name = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='non_urgent')
    arrival_time = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['priority', '-arrival_time']

    def __str__(self):
        return self.case_number


class EmergencyVitalSigns(models.Model):
    case = models.ForeignKey('emergency.EmergencyCase', on_delete=models.CASCADE, related_name='vital_signs')
    recorded_time = models.DateTimeField(default=timezone.now)
    temperature = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    blood_pressure_systolic = models.PositiveIntegerField(null=True, blank=True)
    blood_pressure_diastolic = models.PositiveIntegerField(null=True, blank=True)
    heart_rate = models.PositiveIntegerField(null=True, blank=True)
    respiratory_rate = models.PositiveIntegerField(null=True, blank=True)
    oxygen_saturation = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        null=True, blank=True
    )
    pain_scale = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        null=True, blank=True
    )
    recorded_by = models.ForeignKey('accounts.CustomUser', on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-recorded_time']
        verbose_name_plural = "Emergency Vital Signs"

    def __str__(self):
        return f"Vitals for {self.case.case_number} - {self.recorded_time}"


class EmergencyMedication(models.Model):
    case = models.ForeignKey('emergency.EmergencyCase', on_delete=models.CASCADE, related_name='medications')
    medication_name = models.CharField(max_length=200)
    dosage = models.CharField(max_length=100)
    route = models.CharField(max_length=50)
    frequency = models.CharField(max_length=100)
    administered_time = models.DateTimeField(default=timezone.now)
    administered_by = models.ForeignKey('accounts.CustomUser', on_delete=models.SET_NULL, null=True)
    ordered_by = models.ForeignKey('doctors.Doctor', on_delete=models.SET_NULL, null=True)
    order_time = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, default='ORDERED')
    indication = models.CharField(max_length=300, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-administered_time']

    def __str__(self):
        return f"{self.medication_name} - {self.case.case_number}"


class EmergencyDiagnosticTest(models.Model):
    case = models.ForeignKey('emergency.EmergencyCase', on_delete=models.CASCADE, related_name='diagnostic_tests')
    test_type = models.CharField(max_length=20)
    test_name = models.CharField(max_length=200)
    ordered_by = models.ForeignKey('doctors.Doctor', on_delete=models.SET_NULL, null=True)
    ordered_time = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, default='ORDERED')
    result_time = models.DateTimeField(null=True, blank=True)
    result_summary = models.TextField(blank=True)
    result_file = models.FileField(upload_to='emergency/test_results/', null=True, blank=True)
    priority = models.CharField(max_length=20, default='ROUTINE')
    clinical_indication = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-ordered_time']

    def __str__(self):
        return f"{self.test_name} - {self.case.case_number}"


class EmergencyTransfer(models.Model):
    case = models.ForeignKey('emergency.EmergencyCase', on_delete=models.CASCADE, related_name='transfers')
    transfer_type = models.CharField(max_length=20)
    from_location = models.CharField(max_length=200)
    to_location = models.CharField(max_length=200)
    transfer_time = models.DateTimeField(default=timezone.now)
    transfer_reason = models.TextField()
    condition_on_transfer = models.TextField()
    transferred_by = models.ForeignKey('accounts.CustomUser', on_delete=models.SET_NULL, null=True)
    receiving_doctor = models.ForeignKey('doctors.Doctor', on_delete=models.SET_NULL, null=True, blank=True)
    transport_mode = models.CharField(max_length=20, blank=True)
    equipment_required = models.TextField(blank=True)
    monitoring_required = models.TextField(blank=True)
    transfer_summary = models.TextField()
    medications_transferred = models.TextField(blank=True)

    class Meta:
        ordering = ['-transfer_time']

    def __str__(self):
        return f"Transfer: {self.case.case_number} to {self.to_location}"