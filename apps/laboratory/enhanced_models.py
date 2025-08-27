# Enhanced Laboratory Department Management
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal
from apps.accounts.models import CustomUser as User
from apps.patients.models import Patient
from apps.doctors.models import Doctor
from apps.core.utils.serial_number import SerialNumberMixin
import uuid


class LabDepartment(models.Model):
    """Laboratory departments/sections (Blood, Urine, Biochemistry, etc.)"""
    DEPARTMENT_TYPES = [
        ('hematology', 'Hematology (Blood Tests)'),
        ('clinical_chemistry', 'Clinical Chemistry'),
        ('urinalysis', 'Urinalysis (Urine Tests)'),
        ('microbiology', 'Microbiology'),
        ('immunology', 'Immunology & Serology'),
        ('histopathology', 'Histopathology'),
        ('cytology', 'Cytology'),
        ('molecular', 'Molecular Diagnostics'),
        ('genetics', 'Genetics'),
        ('toxicology', 'Toxicology'),
    ]
    
    name = models.CharField(max_length=100)
    department_type = models.CharField(max_length=50, choices=DEPARTMENT_TYPES)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)
    head_of_department = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='headed_lab_departments')
    
    # Digital signature settings
    requires_digital_signature = models.BooleanField(default=True)
    signature_template = models.TextField(blank=True, help_text="Template for digital signature placement")
    
    # Department settings
    normal_values_template = models.TextField(blank=True, help_text="Standard normal ranges for this department")
    report_header = models.TextField(blank=True)
    report_footer = models.TextField(blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name_plural = "Laboratory Departments"
        
    def __str__(self):
        return f"{self.code} - {self.name}"


class LabTest(models.Model):
    """Individual laboratory tests within departments"""
    department = models.ForeignKey(LabDepartment, on_delete=models.CASCADE, related_name='tests')
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    
    # Test specifications
    sample_type = models.CharField(max_length=100, help_text="Blood, Urine, Stool, etc.")
    sample_volume = models.CharField(max_length=50, blank=True)
    collection_instructions = models.TextField(blank=True)
    
    # Normal ranges and units
    normal_range_male = models.CharField(max_length=100, blank=True)
    normal_range_female = models.CharField(max_length=100, blank=True)
    normal_range_child = models.CharField(max_length=100, blank=True)
    unit = models.CharField(max_length=50, blank=True)
    
    # Processing details
    processing_time = models.CharField(max_length=50, blank=True, help_text="Time to complete test")
    method = models.CharField(max_length=200, blank=True, help_text="Testing method/equipment")
    
    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Status
    is_active = models.BooleanField(default=True)
    requires_fasting = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['department', 'name']
        
    def __str__(self):
        return f"{self.department.code} - {self.name}"


class LabOrder(SerialNumberMixin, models.Model):
    """Laboratory test orders"""
    ORDER_STATUS = [
        ('pending', 'Pending'),
        ('collected', 'Sample Collected'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('reported', 'Reported'),
        ('cancelled', 'Cancelled'),
    ]
    
    PRIORITY_LEVELS = [
        ('routine', 'Routine'),
        ('urgent', 'Urgent'),
        ('stat', 'STAT (Immediate)'),
    ]
    
    # Order details
    order_number = models.CharField(max_length=50, unique=True, blank=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='lab_orders')
    ordered_by = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='lab_orders')
    
    # Order metadata
    order_date = models.DateTimeField(default=timezone.now)
    priority = models.CharField(max_length=20, choices=PRIORITY_LEVELS, default='routine')
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='pending')
    
    # Clinical information
    clinical_diagnosis = models.TextField(blank=True)
    clinical_notes = models.TextField(blank=True)
    
    # Collection details
    sample_collected_at = models.DateTimeField(null=True, blank=True)
    collected_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='collected_samples')
    collection_notes = models.TextField(blank=True)
    
    # Reporting
    report_generated_at = models.DateTimeField(null=True, blank=True)
    reported_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reported_labs')
    
    # Digital signature
    digital_signature = models.TextField(blank=True)
    signature_timestamp = models.DateTimeField(null=True, blank=True)
    signature_ip = models.GenericIPAddressField(null=True, blank=True)
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-order_date']
        
    def __str__(self):
        return f"Lab Order {self.order_number} - {self.patient.full_name}"
        
    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_serial_number('LAB')
        super().save(*args, **kwargs)


class LabOrderItem(models.Model):
    """Individual tests within a lab order"""
    order = models.ForeignKey(LabOrder, on_delete=models.CASCADE, related_name='test_items')
    test = models.ForeignKey(LabTest, on_delete=models.CASCADE)
    
    # Test results
    result_value = models.TextField(blank=True)
    result_text = models.TextField(blank=True)
    interpretation = models.TextField(blank=True)
    
    # Result metadata
    result_date = models.DateTimeField(null=True, blank=True)
    tested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='tested_items')
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_test_items')
    
    # Quality control
    is_abnormal = models.BooleanField(default=False)
    is_critical = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['order', 'test']
        
    def __str__(self):
        return f"{self.order.order_number} - {self.test.name}"


class DigitalSignature(models.Model):
    """Digital signatures for lab reports"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='digital_signatures')
    order = models.ForeignKey(LabOrder, on_delete=models.CASCADE, related_name='signatures')
    
    # Signature details
    signature_data = models.TextField()  # Base64 encoded signature image
    signature_text = models.CharField(max_length=200)
    signature_type = models.CharField(max_length=50, choices=[
        ('doctor', 'Doctor Verification'),
        ('technician', 'Lab Technician'),
        ('pathologist', 'Pathologist'),
        ('supervisor', 'Lab Supervisor'),
    ])
    
    # Security
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Verification
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        
    def __str__(self):
        return f"Signature by {self.user.get_full_name()} - {self.order.order_number}"
