# apps/pharmacy/models.py
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal
from apps.accounts.models import Hospital, User
from apps.patients.models import Patient
from apps.doctors.models import Doctor
import uuid

class DrugCategory(models.Model):
    """Categories for medicines/drugs"""
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='drug_categories')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['hospital', 'name']
        ordering = ['name']
        verbose_name_plural = "Drug Categories"
    
    def __str__(self):
        return self.name


class Manufacturer(models.Model):
    """Medicine manufacturers"""
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='manufacturers')
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20)
    contact_person = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['hospital', 'code']
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Medicine(models.Model):
    """Medicine/Drug inventory"""
    DOSAGE_FORMS = [
        ('TABLET', 'Tablet'),
        ('CAPSULE', 'Capsule'),
        ('SYRUP', 'Syrup'),
        ('INJECTION', 'Injection'),
        ('DROPS', 'Drops'),
        ('OINTMENT', 'Ointment'),
        ('CREAM', 'Cream'),
        ('INHALER', 'Inhaler'),
        ('PATCH', 'Patch'),
        ('OTHER', 'Other'),
    ]
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='medicines')
    medicine_code = models.CharField(max_length=50, unique=True, blank=True)
    
    # Medicine Details
    name = models.CharField(max_length=200)
    generic_name = models.CharField(max_length=200, blank=True)
    brand_name = models.CharField(max_length=200, blank=True)
    manufacturer = models.ForeignKey(Manufacturer, on_delete=models.CASCADE)
    category = models.ForeignKey(DrugCategory, on_delete=models.CASCADE)
    
    # Formulation
    dosage_form = models.CharField(max_length=20, choices=DOSAGE_FORMS)
    strength = models.CharField(max_length=100)  # e.g., "500mg", "10mg/5ml"
    pack_size = models.CharField(max_length=50, blank=True)  # e.g., "10 tablets", "100ml bottle"
    
    # Inventory
    current_stock = models.PositiveIntegerField(default=0)
    reorder_level = models.PositiveIntegerField(default=10)
    maximum_stock = models.PositiveIntegerField(default=1000)
    
    # Pricing
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    mrp = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))], help_text="Maximum Retail Price")
    
    # Expiry and Batch
    batch_number = models.CharField(max_length=50, blank=True)
    manufacturing_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField()
    
    # Medical Information
    composition = models.TextField(blank=True)
    indications = models.TextField(blank=True)
    contraindications = models.TextField(blank=True)
    side_effects = models.TextField(blank=True)
    dosage_instructions = models.TextField(blank=True)
    
    # Status
    is_prescription_required = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    is_discontinued = models.BooleanField(default=False)
    
    # Tracking
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['medicine_code']),
            models.Index(fields=['name']),
            models.Index(fields=['generic_name']),
            models.Index(fields=['expiry_date']),
            models.Index(fields=['current_stock']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.strength}) - {self.manufacturer.name}"
    
    def save(self, *args, **kwargs):
        if not self.medicine_code:
            self.medicine_code = self.generate_medicine_code()
        super().save(*args, **kwargs)
    
    def generate_medicine_code(self):
        """Generate unique medicine code"""
        last_medicine = Medicine.objects.filter(
            hospital=self.hospital
        ).order_by('-created_at').first()
        
        if last_medicine and last_medicine.medicine_code:
            try:
                last_number = int(last_medicine.medicine_code.split('-')[-1])
                new_number = last_number + 1
            except:
                new_number = 1
        else:
            new_number = 1
            
        return f"{self.hospital.code}-MED-{new_number:06d}"
    
    def is_low_stock(self):
        """Check if medicine is low on stock"""
        return self.current_stock <= self.reorder_level
    
    def is_expired(self):
        """Check if medicine is expired"""
        return self.expiry_date < timezone.now().date()
    
    def is_near_expiry(self, days=30):
        """Check if medicine is near expiry"""
        expiry_threshold = timezone.now().date() + timezone.timedelta(days=days)
        return self.expiry_date <= expiry_threshold
    
    def get_stock_status(self):
        """Get stock status with color coding"""
        if self.current_stock == 0:
            return {'status': 'OUT_OF_STOCK', 'color': 'danger', 'text': 'Out of Stock'}
        elif self.is_low_stock():
            return {'status': 'LOW_STOCK', 'color': 'warning', 'text': 'Low Stock'}
        else:
            return {'status': 'IN_STOCK', 'color': 'success', 'text': 'In Stock'}


class Prescription(models.Model):
    """Medical prescriptions"""
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PARTIALLY_DISPENSED', 'Partially Dispensed'),
        ('DISPENSED', 'Dispensed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='prescriptions')
    prescription_number = models.CharField(max_length=20, unique=True, blank=True)
    
    # Medical Information
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='prescriptions')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='prescriptions')
    appointment = models.ForeignKey('appointments.Appointment', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Prescription Details
    prescription_date = models.DateTimeField(default=timezone.now)
    diagnosis = models.TextField(blank=True)
    symptoms = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # Tracking
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Dispensing Information
    dispensed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='dispensed_prescriptions')
    dispensed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['prescription_number']),
            models.Index(fields=['patient']),
            models.Index(fields=['doctor']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Prescription {self.prescription_number} - {self.patient.get_full_name()}"
    
    def save(self, *args, **kwargs):
        if not self.prescription_number:
            self.prescription_number = self.generate_prescription_number()
        super().save(*args, **kwargs)
    
    def generate_prescription_number(self):
        """Generate unique prescription number"""
        from datetime import datetime
        
        today = datetime.now()
        date_str = today.strftime('%Y%m%d')
        
        last_prescription = Prescription.objects.filter(
            hospital=self.hospital,
            created_at__date=today.date()
        ).order_by('-created_at').first()
        
        if last_prescription and last_prescription.prescription_number:
            try:
                last_number = int(last_prescription.prescription_number.split('-')[-1])
                new_number = last_number + 1
            except:
                new_number = 1
        else:
            new_number = 1
            
        return f"{self.hospital.code}-RX-{date_str}-{new_number:04d}"
    
    def get_total_amount(self):
        """Calculate total prescription amount"""
        return sum(item.total_amount for item in self.items.all())


class PrescriptionItem(models.Model):
    """Individual medicines in a prescription"""
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name='items')
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    
    # Dosage Information
    dosage = models.CharField(max_length=100)  # e.g., "1 tablet"
    frequency = models.CharField(max_length=100)  # e.g., "Twice daily"
    duration = models.CharField(max_length=100)  # e.g., "7 days"
    instructions = models.TextField(blank=True)  # e.g., "Take after meals"
    
    # Quantity
    quantity_prescribed = models.PositiveIntegerField()
    quantity_dispensed = models.PositiveIntegerField(default=0)
    
    # Pricing
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        ordering = ['id']
    
    def save(self, *args, **kwargs):
        self.total_amount = self.quantity_prescribed * self.unit_price
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.medicine.name} - {self.dosage} {self.frequency}"
    
    def is_fully_dispensed(self):
        """Check if item is fully dispensed"""
        return self.quantity_dispensed >= self.quantity_prescribed


class PharmacySale(models.Model):
    """Direct pharmacy sales (without prescription)"""
    PAYMENT_METHODS = [
        ('CASH', 'Cash'),
        ('CARD', 'Card'),
        ('UPI', 'UPI'),
        ('OTHER', 'Other'),
    ]
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='pharmacy_sales')
    sale_number = models.CharField(max_length=20, unique=True, blank=True)
    
    # Customer Information (optional for OTC sales)
    patient = models.ForeignKey(Patient, on_delete=models.SET_NULL, null=True, blank=True, related_name='pharmacy_purchases')
    customer_name = models.CharField(max_length=200, blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)
    
    # Sale Details
    sale_date = models.DateTimeField(default=timezone.now)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    net_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # Payment
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='CASH')
    payment_reference = models.CharField(max_length=100, blank=True)
    
    # Tracking
    sold_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Sale {self.sale_number} - {self.net_amount}"
    
    def save(self, *args, **kwargs):
        if not self.sale_number:
            self.sale_number = self.generate_sale_number()
        self.calculate_totals()
        super().save(*args, **kwargs)
    
    def generate_sale_number(self):
        """Generate unique sale number"""
        from datetime import datetime
        
        today = datetime.now()
        date_str = today.strftime('%Y%m%d')
        
        last_sale = PharmacySale.objects.filter(
            hospital=self.hospital,
            created_at__date=today.date()
        ).order_by('-created_at').first()
        
        if last_sale and last_sale.sale_number:
            try:
                last_number = int(last_sale.sale_number.split('-')[-1])
                new_number = last_number + 1
            except:
                new_number = 1
        else:
            new_number = 1
            
        return f"{self.hospital.code}-SALE-{date_str}-{new_number:05d}"
    
    def calculate_totals(self):
        """Calculate sale totals"""
        self.total_amount = sum(item.total_amount for item in self.items.all())
        self.net_amount = self.total_amount - self.discount_amount + self.tax_amount


class PharmacySaleItem(models.Model):
    """Individual items in a pharmacy sale"""
    sale = models.ForeignKey(PharmacySale, on_delete=models.CASCADE, related_name='items')
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        ordering = ['id']
    
    def save(self, *args, **kwargs):
        self.total_amount = self.quantity * self.unit_price
        super().save(*args, **kwargs)
        
        # Update medicine stock
        self.medicine.current_stock -= self.quantity
        self.medicine.save(update_fields=['current_stock'])
    
    def __str__(self):
        return f"{self.medicine.name} x {self.quantity}"


class MedicineStock(models.Model):
    """Medicine stock transactions"""
    TRANSACTION_TYPES = [
        ('PURCHASE', 'Purchase'),
        ('SALE', 'Sale'),
        ('RETURN', 'Return'),
        ('ADJUSTMENT', 'Adjustment'),
        ('EXPIRED', 'Expired'),
        ('DAMAGED', 'Damaged'),
    ]
    
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, related_name='stock_transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    quantity = models.IntegerField()  # Can be negative for outgoing stock
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    reference_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    
    # Tracking
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.medicine.name} - {self.transaction_type} - {self.quantity}"