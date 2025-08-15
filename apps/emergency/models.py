// ...existing code...
    complications = models.TextField(blank=True)
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-treatment_time']
    
    def __str__(self):
        return f"Treatment for {self.case.case_number} - {self.procedure}"


class EmergencyVitalSigns(models.Model):
    """Vital signs monitoring for emergency cases"""
    case = models.ForeignKey(EmergencyCase, on_delete=models.CASCADE, related_name='vital_signs')
    
    # Vital Signs
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
    
    # Additional Measurements
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    height = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    glasgow_coma_scale = models.PositiveIntegerField(
        validators=[MinValueValidator(3), MaxValueValidator(15)],
        null=True, blank=True
    )
    
    # Staff
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    # Notes
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-recorded_time']
        verbose_name_plural = "Emergency Vital Signs"
    
    def __str__(self):
        return f"Vitals for {self.case.case_number} - {self.recorded_time}"


class EmergencyMedication(models.Model):
    """Medications administered in emergency"""
    case = models.ForeignKey(EmergencyCase, on_delete=models.CASCADE, related_name='medications')
    
    # Medication Details
    medication_name = models.CharField(max_length=200)
    dosage = models.CharField(max_length=100)
    route = models.CharField(max_length=50)  # IV, PO, IM, etc.
    frequency = models.CharField(max_length=100)
    
    # Administration
    administered_time = models.DateTimeField(default=timezone.now)
    administered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    # Ordering
    ordered_by = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True)
    order_time = models.DateTimeField(default=timezone.now)
    
    # Status
    STATUS_CHOICES = [
        ('ORDERED', 'Ordered'),
        ('ADMINISTERED', 'Administered'),
        ('HELD', 'Held'),
        ('CANCELLED', 'Cancelled'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ORDERED')
    
    # Notes
    indication = models.CharField(max_length=300, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-administered_time']
    
    def __str__(self):
        return f"{self.medication_name} - {self.case.case_number}"


class EmergencyDiagnosticTest(models.Model):
    """Diagnostic tests ordered in emergency"""
    case = models.ForeignKey(EmergencyCase, on_delete=models.CASCADE, related_name='diagnostic_tests')
    
    TEST_TYPES = [
        ('BLOOD', 'Blood Test'),
        ('URINE', 'Urine Test'),
        ('XRAY', 'X-Ray'),
        ('CT', 'CT Scan'),
        ('MRI', 'MRI'),
        ('ULTRASOUND', 'Ultrasound'),
        ('ECG', 'ECG'),
        ('ECHO', 'Echocardiogram'),
        ('OTHER', 'Other'),
    ]
    
    test_type = models.CharField(max_length=20, choices=TEST_TYPES)
    test_name = models.CharField(max_length=200)
    
    # Ordering
    ordered_by = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True)
    ordered_time = models.DateTimeField(default=timezone.now)
    
    # Status
    STATUS_CHOICES = [
        ('ORDERED', 'Ordered'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ORDERED')
    
    # Results
    result_time = models.DateTimeField(null=True, blank=True)
    result_summary = models.TextField(blank=True)
    result_file = models.FileField(upload_to='emergency/test_results/', null=True, blank=True)
    
    # Priority
    PRIORITY_CHOICES = [
        ('STAT', 'STAT'),
        ('URGENT', 'Urgent'),
        ('ROUTINE', 'Routine'),
    ]
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='ROUTINE')
    
    # Notes
    clinical_indication = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-ordered_time']
    
    def __str__(self):
        return f"{self.test_name} - {self.case.case_number}"


class EmergencyTransfer(models.Model):
    """Transfer records for emergency cases"""
    case = models.ForeignKey(EmergencyCase, on_delete=models.CASCADE, related_name='transfers')
    
    TRANSFER_TYPES = [
        ('INTERNAL', 'Internal Transfer'),
        ('EXTERNAL', 'External Transfer'),
        ('ICU', 'ICU Transfer'),
        ('WARD', 'Ward Transfer'),
        ('OR', 'Operating Room'),
    ]
    
    transfer_type = models.CharField(max_length=20, choices=TRANSFER_TYPES)
    
    # From/To Information
    from_location = models.CharField(max_length=200)
    to_location = models.CharField(max_length=200)
    to_hospital = models.ForeignKey(Hospital, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Transfer Details
    transfer_time = models.DateTimeField(default=timezone.now)
    transfer_reason = models.TextField()
    condition_on_transfer = models.TextField()
    
    # Staff
    transferred_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    receiving_doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Transport
    TRANSPORT_MODES = [
        ('AMBULANCE', 'Ambulance'),
        ('HELICOPTER', 'Helicopter'),
        ('INTERNAL_TRANSPORT', 'Internal Transport'),
        ('WALKING', 'Walking'),
    ]
    transport_mode = models.CharField(max_length=20, choices=TRANSPORT_MODES)
    
    # Equipment/Monitoring
    equipment_required = models.TextField(blank=True)
    monitoring_required = models.TextField(blank=True)
    
    # Documentation
    transfer_summary = models.TextField()
    medications_transferred = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-transfer_time']
    
    def __str__(self):
        return f"Transfer: {self.case.case_number} to {self.to_location}"