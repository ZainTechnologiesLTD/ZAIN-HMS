# apps/patients/models.py
from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
from apps.tenants.models import Tenant
from apps.accounts.models import CustomUser as User
import uuid
from datetime import date

class Patient(models.Model):
    """Patient model with complete medical information"""
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    BLOOD_GROUP_CHOICES = [
        ('A+', 'A Positive'),
        ('A-', 'A Negative'),
        ('B+', 'B Positive'),
        ('B-', 'B Negative'),
        ('AB+', 'AB Positive'),
        ('AB-', 'AB Negative'),
        ('O+', 'O Positive'),
        ('O-', 'O Negative'),
        ('UNKNOWN', 'Unknown'),
    ]
    
    MARITAL_STATUS_CHOICES = [
        ('SINGLE', 'Single'),
        ('MARRIED', 'Married'),
        ('DIVORCED', 'Divorced'),
        ('WIDOWED', 'Widowed'),
    ]
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hospital = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='patients', null=True, blank=True)
    patient_id = models.CharField(max_length=20, unique=True, blank=True)
    
    # Personal Details
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    blood_group = models.CharField(max_length=10, choices=BLOOD_GROUP_CHOICES, default='UNKNOWN')
    marital_status = models.CharField(max_length=10, choices=MARITAL_STATUS_CHOICES, default='SINGLE')
    
    # Contact Information
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$')
    phone = models.CharField(validators=[phone_regex], max_length=17)
    alternate_phone = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    email = models.EmailField(blank=True)
    
    # Address
    address_line1 = models.CharField(max_length=200)
    address_line2 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default='USA')
    
    # Emergency Contact
    emergency_contact_name = models.CharField(max_length=100)
    emergency_contact_relationship = models.CharField(max_length=50)
    emergency_contact_phone = models.CharField(validators=[phone_regex], max_length=17)
    
    # Medical Information
    allergies = models.TextField(blank=True, help_text="List of known allergies")
    chronic_conditions = models.TextField(blank=True, help_text="Chronic medical conditions")
    current_medications = models.TextField(blank=True, help_text="Current medications")
    medical_history = models.TextField(blank=True, help_text="Relevant medical history")
    family_medical_history = models.TextField(blank=True, help_text="Family medical history")
    
    # Insurance Information
    insurance_provider = models.CharField(max_length=200, blank=True)
    insurance_policy_number = models.CharField(max_length=100, blank=True)
    insurance_group_number = models.CharField(max_length=100, blank=True)
    
    # Profile
    profile_picture = models.ImageField(upload_to='patients/photos/', null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_vip = models.BooleanField(default=False, help_text="VIP patient status")
    
    # Registration Information
    registered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='registered_patients')
    registration_date = models.DateTimeField(auto_now_add=True)
    last_visit = models.DateTimeField(null=True, blank=True)
    
    # Notes
    notes = models.TextField(blank=True, help_text="Additional notes about the patient")
    
    class Meta:
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['patient_id']),
            models.Index(fields=['last_name', 'first_name']),
            models.Index(fields=['phone']),
            models.Index(fields=['registration_date']),
        ]
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.patient_id})"
    
    def save(self, *args, **kwargs):
        """Override save to handle cross-database relationships and generate patient ID"""
        if not self.patient_id:
            self.patient_id = self.generate_patient_id()
        
        using = kwargs.get('using', 'default')
        
        # If saving to a tenant database, temporarily disable foreign key checks
        if using and using != 'default':
            from django.db import connections
            connection = connections[using]
            with connection.cursor() as cursor:
                cursor.execute("PRAGMA foreign_keys=OFF")
                try:
                    super().save(*args, **kwargs)
                finally:
                    cursor.execute("PRAGMA foreign_keys=ON")
        else:
            super().save(*args, **kwargs)
    
    def delete(self, using=None, keep_parents=False):
        """Override delete to handle cross-database relationships"""
        if using and using != 'default':
            from django.db import connections
            connection = connections[using]
            with connection.cursor() as cursor:
                cursor.execute("PRAGMA foreign_keys=OFF")
                try:
                    super().delete(using=using, keep_parents=keep_parents)
                finally:
                    cursor.execute("PRAGMA foreign_keys=ON")
        else:
            super().delete(using=using, keep_parents=keep_parents)

    def generate_patient_id(self):
        """Generate unique patient ID"""
        last_patient = Patient.objects.filter(
            hospital=self.hospital
        ).order_by('-registration_date').first()
        
        if last_patient and last_patient.patient_id:
            try:
                last_number = int(last_patient.patient_id.split('-')[-1])
                new_number = last_number + 1
            except:
                new_number = 1
        else:
            new_number = 1
            
        return f"{self.hospital.subdomain}-PAT-{new_number:06d}"
    
    def get_full_name(self):
        """Return full name"""
        parts = [self.first_name, self.middle_name, self.last_name]
        return ' '.join(filter(None, parts))
    
    def get_age(self):
        """Calculate age"""
        today = date.today()
        return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
    
    def get_full_address(self):
        """Return formatted address"""
        parts = [
            self.address_line1,
            self.address_line2,
            self.city,
            self.state,
            self.postal_code,
            self.country
        ]
        return ', '.join(filter(None, parts))


class PatientDocument(models.Model):
    """Patient documents and files"""
    DOCUMENT_TYPES = [
        ('ID', 'Identity Document'),
        ('INSURANCE', 'Insurance Card'),
        ('MEDICAL_RECORD', 'Medical Record'),
        ('LAB_RESULT', 'Lab Result'),
        ('PRESCRIPTION', 'Prescription'),
        ('XRAY', 'X-Ray'),
        ('MRI', 'MRI'),
        ('CT_SCAN', 'CT Scan'),
        ('OTHER', 'Other'),
    ]
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='patients/documents/')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_confidential = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.patient.get_full_name()} - {self.title}"


class PatientNote(models.Model):
    """Patient notes and observations"""
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='patient_notes')
    note = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_private = models.BooleanField(default=False, help_text="Private notes visible only to doctors")
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Note for {self.patient.get_full_name()} by {self.created_by}"


class PatientVitals(models.Model):
    """Patient vital signs"""
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='vitals')
    
    # Vital Signs
    temperature = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True, help_text="Temperature in Fahrenheit")
    blood_pressure_systolic = models.PositiveIntegerField(null=True, blank=True)
    blood_pressure_diastolic = models.PositiveIntegerField(null=True, blank=True)
    heart_rate = models.PositiveIntegerField(null=True, blank=True, help_text="Beats per minute")
    respiratory_rate = models.PositiveIntegerField(null=True, blank=True, help_text="Breaths per minute")
    oxygen_saturation = models.PositiveIntegerField(null=True, blank=True, help_text="SpO2 percentage")
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Weight in kg")
    height = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Height in cm")
    bmi = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True, help_text="BMI calculated")
    
    # Additional Measurements
    notes = models.TextField(blank=True)
    
    # Record Information
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    recorded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-recorded_at']
        verbose_name_plural = "Patient Vitals"
    
    def save(self, *args, **kwargs):
        # Calculate BMI if weight and height are provided
        if self.weight and self.height:
            height_m = float(self.height) / 100  # Convert cm to meters
            self.bmi = float(self.weight) / (height_m * height_m)
        super().save(*args, **kwargs)
    
    def get_blood_pressure(self):
        """Return formatted blood pressure"""
        if self.blood_pressure_systolic and self.blood_pressure_diastolic:
            return f"{self.blood_pressure_systolic}/{self.blood_pressure_diastolic}"
        return ""
    
    def __str__(self):
        return f"Vitals for {self.patient.get_full_name()} on {self.recorded_at.date()}"
