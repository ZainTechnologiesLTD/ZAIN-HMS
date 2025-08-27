# apps/radiology/models.py
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal
# # from tenants.models import  # Temporarily commented Tenant  # Temporarily commented
from apps.accounts.models import CustomUser as User
from apps.patients.models import Patient
from apps.doctors.models import Doctor
from apps.core.utils.serial_number import SerialNumberMixin
import uuid


class StudyType(models.Model):
    """Types of radiological studies/examinations"""
    
    MODALITY_CHOICES = [
        ('X_RAY', 'X-Ray'),
        ('CT', 'CT Scan'),
        ('MRI', 'MRI'),
        ('ULTRASOUND', 'Ultrasound'),
        ('MAMMOGRAPHY', 'Mammography'),
        ('FLUOROSCOPY', 'Fluoroscopy'),
        ('NUCLEAR', 'Nuclear Medicine'),
        ('PET', 'PET Scan'),
        ('DEXA', 'DEXA Scan'),
    ]
    
    BODY_PART_CHOICES = [
        ('HEAD', 'Head'),
        ('NECK', 'Neck'),
        ('CHEST', 'Chest'),
        ('ABDOMEN', 'Abdomen'),
        ('PELVIS', 'Pelvis'),
        ('SPINE', 'Spine'),
        ('UPPER_LIMB', 'Upper Limb'),
        ('LOWER_LIMB', 'Lower Limb'),
        ('WHOLE_BODY', 'Whole Body'),
    ]
    
    # tenant = models.ForeignKey(Tenant  # Temporarily commented, on_delete=models.CASCADE, related_name='study_types')
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True, blank=True)
    description = models.TextField(blank=True)
    
    # Technical Details
    modality = models.CharField(max_length=20, choices=MODALITY_CHOICES)
    body_part = models.CharField(max_length=20, choices=BODY_PART_CHOICES, blank=True)
    
    # Preparation and Instructions
    preparation_instructions = models.TextField(blank=True, help_text="Instructions for patient preparation")
    contrast_required = models.BooleanField(default=False)
    fasting_required = models.BooleanField(default=False)
    
    # Pricing and Timing
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    estimated_duration_minutes = models.PositiveIntegerField(default=30)
    reporting_time_hours = models.PositiveIntegerField(default=24)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Tracking
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.generate_code()
        super().save(*args, **kwargs)
    
    def generate_code(self):
        """Generate unique study code"""
        last_study = StudyType.objects.order_by('-created_at').first()
        if last_study and last_study.code:
            try:
                last_number = int(last_study.code.split('-')[-1])
                new_number = last_number + 1
            except Exception:
                new_number = 1
        else:
            new_number = 1
        return f"RAD-{new_number:05d}"


class RadiologyOrder(SerialNumberMixin):
    """Radiology examination orders"""
    
    SERIAL_TYPE = 'radiology_order'  # For automatic serial number generation
    
    STATUS_CHOICES = [
        ('ORDERED', 'Ordered'),
        ('SCHEDULED', 'Scheduled'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('REPORTED', 'Reported'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    PRIORITY_CHOICES = [
        ('ROUTINE', 'Routine'),
        ('URGENT', 'Urgent'),
        ('EMERGENCY', 'Emergency'),
        ('STAT', 'STAT'),
    ]
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # tenant = models.ForeignKey(Tenant  # Temporarily commented, on_delete=models.CASCADE, related_name='radiology_orders')
    order_number = models.CharField(max_length=20, unique=True, blank=True)
    
    # Patient and Doctor Information
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='radiology_orders')
    ordering_doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='ordered_radiology_studies')
    appointment = models.ForeignKey('appointments.Appointment', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Order Details
    order_date = models.DateTimeField(default=timezone.now)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='ROUTINE')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ORDERED')
    
    # Clinical Information
    clinical_history = models.TextField(blank=True)
    clinical_indication = models.TextField(blank=True)
    provisional_diagnosis = models.TextField(blank=True)
    special_instructions = models.TextField(blank=True)
    
    # Scheduling
    scheduled_date = models.DateTimeField(null=True, blank=True)
    scheduled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='scheduled_radiology_orders')
    
    # Completion
    completed_at = models.DateTimeField(null=True, blank=True)
    technologist = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='performed_radiology_studies')
    
    # Reporting
    reported_at = models.DateTimeField(null=True, blank=True)
    radiologist = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reported_radiology_studies')
    
    # Financials
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    net_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    is_paid = models.BooleanField(default=False)
    
    # Tracking
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_radiology_orders')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order_number']),
            models.Index(fields=['patient']),
            models.Index(fields=['ordering_doctor']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Radiology Order {self.order_number} - {self.patient.get_full_name()}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        self.calculate_totals()
        super().save(*args, **kwargs)
    
    def generate_order_number(self):
        """Generate unique order number"""
        from datetime import datetime
        
        today = datetime.now()
        date_str = today.strftime('%Y%m%d')
        
        last_order = RadiologyOrder.objects.filter(
            created_at__date=today.date()
        ).order_by('-created_at').first()
        
        if last_order and last_order.order_number:
            try:
                last_number = int(last_order.order_number.split('-')[-1])
                new_number = last_number + 1
            except:
                new_number = 1
        else:
            new_number = 1
        return f"RAD-{date_str}-{new_number:04d}"
    
    def calculate_totals(self):
        """Calculate order totals from items"""
        total = sum(item.price for item in self.items.all())
        self.total_amount = total
        self.net_amount = total - self.discount_amount


class RadiologyOrderItem(models.Model):
    """Individual studies in a radiology order"""
    order = models.ForeignKey(RadiologyOrder, on_delete=models.CASCADE, related_name='items')
    study_type = models.ForeignKey(StudyType, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Study-specific details
    laterality = models.CharField(max_length=20, choices=[
        ('LEFT', 'Left'),
        ('RIGHT', 'Right'),
        ('BILATERAL', 'Bilateral'),
        ('NA', 'Not Applicable'),
    ], default='NA')
    
    # Status tracking for individual studies
    status = models.CharField(max_length=20, choices=RadiologyOrder.STATUS_CHOICES, default='ORDERED')
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['id']
    
    def save(self, *args, **kwargs):
        if not self.price:
            self.price = self.study_type.price
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.study_type.name} - {self.order.order_number}"


class ImagingStudy(models.Model):
    """Completed imaging studies with results"""
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending Review'),
        ('PRELIMINARY', 'Preliminary Report'),
        ('FINAL', 'Final Report'),
        ('AMENDED', 'Amended Report'),
    ]
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_item = models.OneToOneField(RadiologyOrderItem, on_delete=models.CASCADE, related_name='study')
    study_instance_uid = models.CharField(max_length=64, unique=True, blank=True)
    
    # Study Metadata
    study_date = models.DateTimeField(default=timezone.now)
    modality = models.CharField(max_length=20, choices=StudyType.MODALITY_CHOICES)
    body_part = models.CharField(max_length=20, choices=StudyType.BODY_PART_CHOICES, blank=True)
    
    # Technical Parameters
    technique = models.TextField(blank=True)
    contrast_used = models.BooleanField(default=False)
    contrast_agent = models.CharField(max_length=100, blank=True)
    
    # Quality Control
    study_quality = models.CharField(max_length=20, choices=[
        ('EXCELLENT', 'Excellent'),
        ('GOOD', 'Good'),
        ('ADEQUATE', 'Adequate'),
        ('POOR', 'Poor'),
        ('NON_DIAGNOSTIC', 'Non-diagnostic'),
    ], default='GOOD')
    
    # Images and Files
    image_count = models.PositiveIntegerField(default=0)
    dicom_storage_path = models.CharField(max_length=500, blank=True)
    
    # Reporting
    findings = models.TextField(blank=True)
    impression = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)
    
    # Status and Review
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    reported_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='radiologist_reports')
    reported_at = models.DateTimeField(null=True, blank=True)
    
    # Peer Review
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_studies')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    # Critical Findings
    is_critical = models.BooleanField(default=False)
    critical_findings = models.TextField(blank=True)
    critical_notified_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-study_date']
    
    def __str__(self):
        return f"{self.order_item.study_type.name} - {self.study_date.strftime('%Y-%m-%d')}"
    
    def get_patient(self):
        """Get patient from order item"""
        return self.order_item.order.patient
    
    def get_ordering_doctor(self):
        """Get ordering doctor from order item"""
        return self.order_item.order.ordering_doctor


class ImagingImage(models.Model):
    """Individual images within an imaging study"""
    study = models.ForeignKey(ImagingStudy, on_delete=models.CASCADE, related_name='images')
    image_file = models.ImageField(upload_to='radiology/images/')
    dicom_file = models.FileField(upload_to='radiology/dicom/', null=True, blank=True)
    
    # Image Metadata
    series_number = models.PositiveIntegerField(default=1)
    instance_number = models.PositiveIntegerField(default=1)
    slice_thickness = models.FloatField(null=True, blank=True)
    window_center = models.IntegerField(null=True, blank=True)
    window_width = models.IntegerField(null=True, blank=True)
    
    # Image Details
    description = models.CharField(max_length=200, blank=True)
    view_position = models.CharField(max_length=50, blank=True)  # AP, PA, LAT, etc.
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['series_number', 'instance_number']
    
    def __str__(self):
        return f"Image {self.instance_number} - {self.study}"


class RadiologyEquipment(models.Model):
    """Radiology equipment management"""
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('MAINTENANCE', 'Under Maintenance'),
        ('CALIBRATION', 'Calibration Due'),
        ('OUT_OF_ORDER', 'Out of Order'),
        ('RETIRED', 'Retired'),
    ]
    
    # tenant = models.ForeignKey(Tenant  # Temporarily commented, on_delete=models.CASCADE, related_name='radiology_equipment')
    name = models.CharField(max_length=200)
    equipment_type = models.CharField(max_length=20, choices=StudyType.MODALITY_CHOICES)
    manufacturer = models.CharField(max_length=100, blank=True)
    model = models.CharField(max_length=100, blank=True)
    serial_number = models.CharField(max_length=100, blank=True)
    
    # Location
    room_number = models.CharField(max_length=50, blank=True)
    location_description = models.CharField(max_length=200, blank=True)
    
    # Status and Maintenance
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    installation_date = models.DateField(null=True, blank=True)
    last_maintenance = models.DateField(null=True, blank=True)
    next_maintenance = models.DateField(null=True, blank=True)
    
    # Usage Tracking
    total_studies = models.PositiveIntegerField(default=0)
    
    # Notes
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        
    def __str__(self):
        return f"{self.name} ({self.get_equipment_type_display()})"
