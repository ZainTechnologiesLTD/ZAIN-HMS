# apps/laboratory/models.py
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

class LabSection(models.Model):
    """Laboratory sections/departments (Blood, Urine, etc.)"""
    # tenant = models.ForeignKey(Tenant  # Temporarily commented, on_delete=models.CASCADE, related_name='lab_sections')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)
    head_of_section = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='headed_lab_sections')
    is_active = models.BooleanField(default=True)
    
    # Digital signature settings for this section
    requires_digital_signature = models.BooleanField(default=True)
    signature_template = models.TextField(blank=True, help_text="Template for digital signature placement")
    
    # Reporting settings
    report_header = models.TextField(blank=True)
    report_footer = models.TextField(blank=True)
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name_plural = "Laboratory Sections"
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class TestCategory(models.Model):
    """Categories for laboratory tests within sections"""
    # tenant = models.ForeignKey(Tenant  # Temporarily commented, on_delete=models.CASCADE, related_name='test_categories')
    section = models.ForeignKey(LabSection, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    # Test ordering within section
    display_order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['section', 'display_order', 'name']
        verbose_name_plural = "Test Categories"
        unique_together = [['section', 'name']]
    
    def __str__(self):
        return f"{self.section.code} - {self.name}"


class LabTest(models.Model):
    """Laboratory test definitions"""
    SAMPLE_TYPES = [
        ('BLOOD', 'Blood'),
        ('URINE', 'Urine'),
        ('STOOL', 'Stool'),
        ('SPUTUM', 'Sputum'),
        ('CSF', 'Cerebrospinal Fluid'),
        ('TISSUE', 'Tissue'),
        ('SWAB', 'Swab'),
        ('OTHER', 'Other'),
    ]
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # tenant = models.ForeignKey(Tenant  # Temporarily commented, on_delete=models.CASCADE, related_name='lab_tests', default=1)
    test_code = models.CharField(max_length=20, unique=True, blank=True)
    
    # Test Details
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.ForeignKey(TestCategory, on_delete=models.CASCADE, related_name='tests', default=1)
    
    # Sample Information
    sample_type = models.CharField(max_length=20, choices=SAMPLE_TYPES)
    sample_volume = models.CharField(max_length=50, blank=True)
    collection_instructions = models.TextField(blank=True)
    
    # Pricing and Time
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    reporting_time_hours = models.PositiveIntegerField(default=24)
    
    # Reference Values
    reference_range_male = models.CharField(max_length=200, blank=True)
    reference_range_female = models.CharField(max_length=200, blank=True)
    reference_range_child = models.CharField(max_length=200, blank=True)
    units = models.CharField(max_length=50, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    requires_fasting = models.BooleanField(default=False)
    
    # Tracking
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['test_code']),
            models.Index(fields=['name']),
            models.Index(fields=['category']),
        ]
    
    def __str__(self):
        return f"{self.test_code} - {self.name}"
    
    def save(self, *args, **kwargs):
        if not self.test_code:
            self.test_code = self.generate_test_code()
        super().save(*args, **kwargs)
    
    def generate_test_code(self):
        """Generate unique test code"""
        last_test = LabTest.objects.order_by('-created_at').first()
        if last_test and last_test.test_code:
            try:
                last_number = int(last_test.test_code.split('-')[-1])
                new_number = last_number + 1
            except Exception:
                new_number = 1
        else:
            new_number = 1
        return f"LAB-{new_number:05d}"


class LabOrder(SerialNumberMixin):
    """Laboratory test orders"""
    
    SERIAL_TYPE = 'lab_order'  # For automatic serial number generation
    STATUS_CHOICES = [
        ('ORDERED', 'Ordered'),
        ('SAMPLE_COLLECTED', 'Sample Collected'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    PRIORITY_CHOICES = [
        ('ROUTINE', 'Routine'),
        ('URGENT', 'Urgent'),
        ('EMERGENCY', 'Emergency'),
    ]
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # tenant = models.ForeignKey(Tenant  # Temporarily commented, on_delete=models.CASCADE, related_name='lab_orders')
    order_number = models.CharField(max_length=20, unique=True, blank=True)
    
    # Patient and Doctor Information
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='lab_orders')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='lab_orders')
    appointment = models.ForeignKey('appointments.Appointment', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Order Details
    order_date = models.DateTimeField(default=timezone.now)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='ROUTINE')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ORDERED')
    
    # Clinical Information
    clinical_history = models.TextField(blank=True)
    provisional_diagnosis = models.TextField(blank=True)
    special_instructions = models.TextField(blank=True)
    
    # Sample Collection
    sample_collected_at = models.DateTimeField(null=True, blank=True)
    sample_collected_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='collected_samples')
    
    # Completion
    completed_at = models.DateTimeField(null=True, blank=True)
    completed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='completed_lab_orders')
    
    # Financials
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    net_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    is_paid = models.BooleanField(default=False)
    
    # Tracking
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_lab_orders')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order_number']),
            models.Index(fields=['patient']),
            models.Index(fields=['doctor']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Lab Order {self.order_number} - {self.patient.get_full_name()}"
    
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
        # Tenant disabled: find last order created today globally
        last_order = LabOrder.objects.filter(
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
        return f"LO-{date_str}-{new_number:04d}"
    
    def calculate_totals(self):
        """Calculate order totals"""
        self.total_amount = sum(item.price for item in self.items.all())
        self.net_amount = self.total_amount - self.discount_amount
    
    def get_status_color(self):
        """Return Bootstrap color class for status"""
        colors = {
            'ORDERED': 'secondary',
            'SAMPLE_COLLECTED': 'info',
            'IN_PROGRESS': 'warning',
            'COMPLETED': 'success',
            'CANCELLED': 'danger',
        }
        return colors.get(self.status, 'secondary')
    
    def get_expected_completion(self):
        """Calculate expected completion time"""
        if self.sample_collected_at:
            max_hours = max(item.test.reporting_time_hours for item in self.items.all()) if self.items.exists() else 24
            return self.sample_collected_at + timezone.timedelta(hours=max_hours)
        return None


class LabOrderItem(models.Model):
    """Individual tests in a lab order"""
    order = models.ForeignKey(LabOrder, on_delete=models.CASCADE, related_name='items')
    test = models.ForeignKey(LabTest, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Status tracking for individual tests
    status = models.CharField(max_length=20, choices=LabOrder.STATUS_CHOICES, default='ORDERED')
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['id']
    
    def save(self, *args, **kwargs):
        if not self.price:
            self.price = self.test.price
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.test.name} - {self.order.order_number}"


class LabResult(models.Model):
    """Laboratory test results"""
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PENDING_REVIEW', 'Pending Review'),
        ('REVIEWED', 'Reviewed'),
        ('REPORTED', 'Reported'),
    ]
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_item = models.OneToOneField(LabOrderItem, on_delete=models.CASCADE, related_name='result', default=1)
    
    # Result Data
    result_value = models.TextField()
    result_unit = models.CharField(max_length=50, blank=True)
    reference_range = models.CharField(max_length=200, blank=True)
    is_abnormal = models.BooleanField(default=False)
    abnormal_flag = models.CharField(max_length=10, blank=True)  # H, L, HH, LL
    
    # Additional Information
    methodology = models.CharField(max_length=200, blank=True)
    comments = models.TextField(blank=True)
    interpretation = models.TextField(blank=True)
    
    # Quality Control
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='performed_tests')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_tests')
    
    # Timestamps
    performed_at = models.DateTimeField(default=timezone.now)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reported_at = models.DateTimeField(null=True, blank=True)
    
    # File Attachments
    result_file = models.FileField(upload_to='lab_results/', null=True, blank=True)
    
    class Meta:
        ordering = ['-performed_at']
    
    def __str__(self):
        return f"Result for {self.order_item.test.name} - {self.order_item.order.patient.get_full_name()}"
    
    def get_patient(self):
        """Get patient from order item"""
        return self.order_item.order.patient
    
    def get_doctor(self):
        """Get doctor from order item"""
        return self.order_item.order.doctor
    
    def mark_abnormal_if_needed(self):
        """Automatically mark result as abnormal based on reference range"""
        # This would contain logic to compare result_value with reference_range
        # For now, it's a placeholder for business logic
        pass


class LabEquipment(models.Model):
    """Laboratory equipment management"""
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('MAINTENANCE', 'Under Maintenance'),
        ('CALIBRATION', 'Calibration Due'),
        ('OUT_OF_ORDER', 'Out of Order'),
        ('RETIRED', 'Retired'),
    ]
    
    # tenant = models.ForeignKey(Tenant  # Temporarily commented, on_delete=models.CASCADE, related_name='lab_equipment')
    name = models.CharField(max_length=200)
    model = models.CharField(max_length=100)
    manufacturer = models.CharField(max_length=100)
    serial_number = models.CharField(max_length=100, unique=True)
    
    # Location and Usage
    location = models.CharField(max_length=100)
    tests = models.ManyToManyField(LabTest, blank=True, related_name='required_equipment')
    
    # Maintenance
    purchase_date = models.DateField()
    warranty_expiry = models.DateField(null=True, blank=True)
    last_maintenance = models.DateField(null=True, blank=True)
    next_maintenance = models.DateField(null=True, blank=True)
    last_calibration = models.DateField(null=True, blank=True)
    next_calibration = models.DateField(null=True, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    notes = models.TextField(blank=True)
    
    # Tracking
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.model})"
    
    def is_maintenance_due(self):
        """Check if maintenance is due"""
        if self.next_maintenance:
            return self.next_maintenance <= timezone.now().date()
        return False
    
    def is_calibration_due(self):
        """Check if calibration is due"""
        if self.next_calibration:
            return self.next_calibration <= timezone.now().date()
        return False


class DigitalSignature(models.Model):
    """Digital signatures for laboratory reports"""
    SIGNATURE_TYPE_CHOICES = [
        ('PERFORMED', 'Test Performed By'),
        ('REVIEWED', 'Reviewed By'),
        ('APPROVED', 'Approved By'),
        ('CONSULTANT', 'Consultant Signature'),
    ]
    
    # tenant = models.ForeignKey(Tenant  # Temporarily commented, on_delete=models.CASCADE, related_name='digital_signatures')
    lab_result = models.ForeignKey(LabResult, on_delete=models.CASCADE, related_name='signatures')
    
    # Signature Details
    signature_type = models.CharField(max_length=20, choices=SIGNATURE_TYPE_CHOICES)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='lab_signatures')
    
    # Digital signature data
    signature_image = models.ImageField(upload_to='signatures/lab/', null=True, blank=True)
    signature_text = models.TextField(blank=True, help_text="Text-based signature")
    
    # Verification
    signed_at = models.DateTimeField(auto_now_add=True)
    signature_hash = models.CharField(max_length=64, blank=True)  # SHA-256 hash for verification
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    # Position on report
    position_x = models.FloatField(default=0.0, help_text="X coordinate on report")
    position_y = models.FloatField(default=0.0, help_text="Y coordinate on report")
    
    class Meta:
        ordering = ['-signed_at']
        unique_together = [['lab_result', 'signature_type', 'doctor']]
    
    def __str__(self):
        return f"{self.signature_type} signature by {self.doctor} on {self.signed_at.date()}"
    
    def generate_signature_hash(self):
        """Generate hash for signature verification"""
        import hashlib
        data = f"{self.lab_result.id}-{self.doctor.id}-{self.signed_at.isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    def save(self, *args, **kwargs):
        if not self.signature_hash:
            self.signature_hash = self.generate_signature_hash()
        super().save(*args, **kwargs)


class LabReportTemplate(models.Model):
    """Templates for laboratory report generation"""
    # tenant = models.ForeignKey(Tenant  # Temporarily commented, on_delete=models.CASCADE, related_name='lab_report_templates')
    section = models.ForeignKey(LabSection, on_delete=models.CASCADE, related_name='report_templates')
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Template content
    header_html = models.TextField(blank=True)
    body_html = models.TextField()
    footer_html = models.TextField(blank=True)
    
    # CSS styling
    css_styles = models.TextField(blank=True)
    
    # Template settings
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # Signature placement
    signature_positions = models.JSONField(default=dict, blank=True, help_text="JSON defining signature positions")
    
    # Tracking
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['section', 'name']
        unique_together = [['section', 'name']]
    
    def __str__(self):
        return f"{self.section.name} - {self.name}"
    
    def save(self, *args, **kwargs):
        # Ensure only one default template per section
        if self.is_default:
            LabReportTemplate.objects.filter(
                section=self.section, 
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)