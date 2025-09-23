# apps/laboratory/models.py
# Consolidated Laboratory Management System Models

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from decimal import Decimal
from apps.accounts.models import CustomUser as User
from apps.patients.models import Patient
from apps.doctors.models import Doctor
from apps.core.utils.serial_number import SerialNumberMixin
import uuid


class LabSection(models.Model):
    """Laboratory sections/departments (Blood, Urine, Biochemistry, etc.)"""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)
    head_of_section = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='headed_lab_sections')
    is_active = models.BooleanField(default=True)
    
    # Digital signature settings for this section
    requires_digital_signature = models.BooleanField(default=False)
    signature_authority = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='signature_lab_sections')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'laboratory_labsection'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"


class LabTest(models.Model):
    """Laboratory tests available in each section"""
    section = models.ForeignKey(LabSection, on_delete=models.CASCADE, related_name='tests')
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    
    # Pricing
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # Test parameters
    normal_range = models.CharField(max_length=200, blank=True)
    normal_range_child = models.CharField(max_length=200, blank=True)
    unit = models.CharField(max_length=50, blank=True)
    
    # Timing and scheduling
    sample_collection_time = models.DurationField(null=True, blank=True, help_text="Time required for sample collection")
    processing_time = models.DurationField(null=True, blank=True, help_text="Time required to process the test")
    
    # Status and availability
    is_active = models.BooleanField(default=True)
    requires_fasting = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'laboratory_labtest'
        ordering = ['section__name', 'name']

    def __str__(self):
        return f"{self.name} ({self.code})"

    def get_age_appropriate_range(self, patient):
        """Get normal range based on patient age"""
        if not patient or not patient.date_of_birth:
            return self.normal_range
        
        # Calculate age
        today = timezone.now().date()
        age = today.year - patient.date_of_birth.year
        if today < patient.date_of_birth.replace(year=today.year):
            age -= 1

        # Return child range if under 18    
        if age < 18 and self.normal_range_child:
            return self.normal_range_child
        return self.normal_range


class LabOrder(SerialNumberMixin):
    """Laboratory test orders"""
    SERIAL_TYPE = 'lab_order'  # For automatic serial number generation
    
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('sample_collected', _('Sample Collected')),
        ('in_progress', _('In Progress')), 
        ('completed', _('Completed')),
        ('cancelled', _('Cancelled')),
        ('reported', _('Reported')),
    ]

    PRIORITY_CHOICES = [
        ('routine', _('Routine')),
        ('urgent', _('Urgent')),
        ('stat', _('STAT')),
    ]

    # Basic order information
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='lab_orders')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='lab_orders')
    order_number = models.CharField(max_length=20, unique=True, blank=True)
    
    # Order details
    order_date = models.DateTimeField(auto_now_add=True)
    sample_collected_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='routine')
    
    # Clinical information
    clinical_history = models.TextField(blank=True, help_text="Clinical notes and patient history")
    provisional_diagnosis = models.TextField(blank=True)
    special_instructions = models.TextField(blank=True)
    
    # Financial information
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    net_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    is_paid = models.BooleanField(default=False)
    
    # User relationships to match database
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_lab_orders')
    completed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                      related_name='completed_lab_orders')
    sample_collected_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                          related_name='collected_lab_orders')
    appointment = models.ForeignKey('appointments.Appointment', on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'laboratory_laborder'
        ordering = ['-order_date']

    def __str__(self):
        return f"Lab Order {self.order_number} - {self.patient.full_name}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_serial_number()
        
        # Calculate final amount
        if self.total_amount and self.discount:
            discount_amount = (self.total_amount * self.discount) / 100
            self.final_amount = self.total_amount - discount_amount
        else:
            self.final_amount = self.total_amount
            
        super().save(*args, **kwargs)

    def get_tests_summary(self):
        """Get summary of all tests in this order"""
        return ', '.join([item.test.name for item in self.items.all()])


class LabOrderItem(models.Model):
    """Individual test items within a lab order"""
    order = models.ForeignKey(LabOrder, on_delete=models.CASCADE, related_name='items')
    test = models.ForeignKey(LabTest, on_delete=models.CASCADE)
    
    # Pricing for this specific item
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    quantity = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # Test results
    result_value = models.CharField(max_length=200, blank=True)
    result_unit = models.CharField(max_length=50, blank=True)
    normal_range = models.CharField(max_length=200, blank=True)
    
    # Status and flags
    is_abnormal = models.BooleanField(default=False)
    is_critical = models.BooleanField(default=False)
    technician_notes = models.TextField(blank=True)
    
    # Processing information
    sample_collected_at = models.DateTimeField(null=True, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    
    # Staff assignments
    collected_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                     related_name='collected_lab_samples')
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                     related_name='processed_lab_tests')
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                    related_name='verified_lab_results')

    class Meta:
        db_table = 'laboratory_laborderitem'
        unique_together = ['order', 'test']

    def __str__(self):
        return f"{self.order.order_number} - {self.test.name}"

    def save(self, *args, **kwargs):
        # Auto-calculate total price
        self.total_price = self.unit_price * self.quantity
        
        # Set unit price from test if not provided
        if not self.unit_price:
            self.unit_price = self.test.selling_price
            self.total_price = self.unit_price * self.quantity
        
        # Set normal range from test if not provided
        if not self.normal_range and hasattr(self.order, 'patient'):
            self.normal_range = self.test.get_age_appropriate_range(self.order.patient)
        
        super().save(*args, **kwargs)


class LabReport(models.Model):
    """Laboratory test reports"""
    order = models.OneToOneField(LabOrder, on_delete=models.CASCADE, related_name='report')
    report_number = models.CharField(max_length=50, unique=True)
    
    # Report content
    clinical_findings = models.TextField(blank=True)
    interpretation = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)
    
    # Report generation
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='generated_lab_reports')
    
    # Quality assurance
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                    related_name='reviewed_lab_reports')
    
    # Digital signatures for HIPAA compliance
    pathologist_signature = models.TextField(blank=True)
    digital_signature_hash = models.CharField(max_length=128, blank=True)
    
    # Report delivery
    delivered_at = models.DateTimeField(null=True, blank=True)
    delivery_method = models.CharField(max_length=20, choices=[
        ('print', _('Print')),
        ('email', _('Email')),
        ('portal', _('Patient Portal')),
        ('both', _('Print & Email')),
    ], default='print')

    class Meta:
        db_table = 'laboratory_report'
        ordering = ['-generated_at']

    def __str__(self):
        return f"Lab Report {self.report_number} - {self.order.patient.full_name}"

    def save(self, *args, **kwargs):
        if not self.report_number:
            # Generate unique report number
            import uuid
            self.report_number = f"LR-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)


class LabQualityControl(models.Model):
    """Quality control records for laboratory"""
    test = models.ForeignKey(LabTest, on_delete=models.CASCADE, related_name='quality_controls')
    control_date = models.DateField(default=timezone.now)
    
    # QC parameters
    control_lot = models.CharField(max_length=50)
    expected_value = models.CharField(max_length=100)
    actual_value = models.CharField(max_length=100)
    acceptable_range = models.CharField(max_length=100)
    
    # QC status
    is_within_range = models.BooleanField(default=True)
    deviation_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Documentation
    performed_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='performed_qc_tests')
    notes = models.TextField(blank=True)
    corrective_action = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'laboratory_quality_control'
        unique_together = ['test', 'control_date']
        ordering = ['-control_date']

    def __str__(self):
        return f"QC - {self.test.name} ({self.control_date})"


class LabEquipment(models.Model):
    """Laboratory equipment tracking"""
    name = models.CharField(max_length=200)
    model = models.CharField(max_length=100)
    serial_number = models.CharField(max_length=100, unique=True)
    manufacturer = models.CharField(max_length=100)
    
    # Equipment details
    purchase_date = models.DateField()
    warranty_expiry = models.DateField(null=True, blank=True)
    
    # Maintenance
    last_maintenance = models.DateField(null=True, blank=True)
    next_maintenance = models.DateField(null=True, blank=True)
    maintenance_frequency_days = models.PositiveIntegerField(default=365)
    
    # Status
    is_operational = models.BooleanField(default=True)
    location = models.CharField(max_length=100)
    responsible_person = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Associated tests
    supported_tests = models.ManyToManyField(LabTest, blank=True, related_name='equipment')
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'laboratory_labequipment'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.model}"

    @property
    def maintenance_due_soon(self):
        """Check if maintenance is due within 30 days"""
        if not self.next_maintenance:
            return False
        return (self.next_maintenance - timezone.now().date()).days <= 30


# Laboratory Inventory Models
class LabSupply(models.Model):
    """Laboratory supplies and reagents inventory"""
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True)
    category = models.CharField(max_length=100)
    
    # Stock information
    current_stock = models.PositiveIntegerField(default=0)
    minimum_stock = models.PositiveIntegerField(default=10)
    maximum_stock = models.PositiveIntegerField(default=100)
    unit = models.CharField(max_length=20, default='pieces')
    
    # Pricing
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    supplier = models.CharField(max_length=200, blank=True)
    
    # Expiry tracking
    has_expiry = models.BooleanField(default=False)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'laboratory_supply'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"

    @property
    def is_low_stock(self):
        """Check if stock is below minimum level"""
        return self.current_stock <= self.minimum_stock


class LabSupplyBatch(models.Model):
    """Individual batches of laboratory supplies"""
    supply = models.ForeignKey(LabSupply, on_delete=models.CASCADE, related_name='batches')
    batch_number = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField()
    
    # Dates
    received_date = models.DateField(default=timezone.now)
    expiry_date = models.DateField(null=True, blank=True)
    
    # Cost tracking
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    # Status
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'laboratory_supply_batch'
        unique_together = ['supply', 'batch_number']
        ordering = ['expiry_date', 'received_date']

    def __str__(self):
        return f"{self.supply.name} - Batch {self.batch_number}"

    @property
    def is_expired(self):
        """Check if batch is expired"""
        if not self.expiry_date:
            return False
        return timezone.now().date() > self.expiry_date

    @property
    def expires_soon(self):
        """Check if batch expires within 30 days"""
        if not self.expiry_date:
            return False
        return (self.expiry_date - timezone.now().date()).days <= 30