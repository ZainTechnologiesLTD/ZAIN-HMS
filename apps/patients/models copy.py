# models.py
import uuid
from django.utils import timezone
from django.db import models
from django.core.validators import RegexValidator


class Patient(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]

    BLOOD_TYPE_CHOICES = [
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
    ]
# Custom patient ID field
    patient_id = models.CharField(max_length=20, unique=True, blank=True, null=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    age = models.IntegerField(default=0)  # Store calculated age
    gender = models.CharField(max_length=300, choices=GENDER_CHOICES)
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    phone_number = models.CharField(validators=[phone_regex], max_length=100)
    email = models.EmailField(unique=True)
    address = models.TextField()
    image = models.ImageField(upload_to='photos/patients', null=True, blank=True)
    blood_type = models.CharField(max_length=100, choices=BLOOD_TYPE_CHOICES, blank=True, null=True)
    allergies = models.TextField(blank=True)
    medical_conditions = models.TextField(blank=True)
    medications = models.TextField(blank=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(validators=[phone_regex], max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    
    def save(self, *args, **kwargs):
        today = timezone.now().date()
        self.age = today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
             )

        if not self.patient_id:
         self.patient_id = self.generate_unique_patient_id()
    
        super(Patient, self).save(*args, **kwargs)

    def generate_unique_patient_id(self):
        """
        Generate a custom unique ID, e.g., 'PAT-2024-001'.
        """
        # You can modify this format as per your needs
        prefix = "PAT"
        year = timezone.now().year
        unique_suffix = str(uuid.uuid4())[:8]  # Generates a random 8-character string

        # Combine to form a custom patient ID
        return f"{prefix}-{year}-{unique_suffix}"
    
    def __str__(self):
        return f"{self.last_name}, {self.first_name} ({self.patient_id})"

    class Meta:
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['last_name', 'first_name']),
            models.Index(fields=['date_of_birth']),            
        ]
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"  
class MedicalRecord(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='medical_records')
    date = models.DateField()
    doctor_name = models.CharField(max_length=100)
    diagnosis = models.TextField(max_length=100)
    prescription = models.TextField(max_length=500)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.patient} - {self.date}"

    class Meta:
        ordering = ['-date']