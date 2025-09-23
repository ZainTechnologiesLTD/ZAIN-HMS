# apps/pharmacy/models.py
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from apps.accounts.models import CustomUser as User
from apps.patients.models import Patient
from apps.doctors.models import Doctor
import uuid

class DrugCategory(models.Model):
    """Categories for medicines/drugs"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = _('Drug Category')
        verbose_name_plural = _('Drug Categories')
    
    def __str__(self):
        return self.name


class Manufacturer(models.Model):
    """Medicine manufacturers"""
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20)
    contact_person = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = _('Manufacturer')
        verbose_name_plural = _('Manufacturers')
    
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
    medicine_code = models.CharField(max_length=50, unique=True, blank=True)
    
    # Medicine Details
    name = models.CharField(max_length=200)
    generic_name = models.CharField(max_length=200, blank=True)
    brand_name = models.CharField(max_length=200, blank=True)
    manufacturer = models.ForeignKey(Manufacturer, on_delete=models.CASCADE, default=1)
    category = models.ForeignKey(DrugCategory, on_delete=models.CASCADE, default=1)
    
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
    expiry_date = models.DateField(default='2025-12-31')
    
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
        verbose_name = _('Medicine')
        verbose_name_plural = _('Medicines')
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
        last_medicine = Medicine.objects.order_by('-created_at').first()
        if last_medicine and last_medicine.medicine_code:
            try:
                last_number = int(last_medicine.medicine_code.split('-')[-1])
                new_number = last_number + 1
            except Exception:
                new_number = 1
        else:
            new_number = 1
        return f"MED-{new_number:06d}"
    
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
            
        return f"ZAIN-RX-{date_str}-{new_number:04d}"
    
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
    sale_number = models.CharField(max_length=20, unique=True, blank=True)
    
    # Customer Information (optional for OTC sales)
    patient = models.ForeignKey(Patient, on_delete=models.SET_NULL, null=True, blank=True, related_name='pharmacy_sales')
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
            
        return f"ZAIN-SALE-{date_str}-{new_number:05d}"
    
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
        verbose_name = _('Medicine Stock')
        verbose_name_plural = _('Medicine Stocks')
    
    def __str__(self):
        return f"{self.medicine.name} - {self.transaction_type} - {self.quantity}"


# Pharmacy PoS System Models

class PharmacyPoSTransaction(models.Model):
    """Pharmacy Point of Sale transactions - separate from billing PoS"""
    
    PAYMENT_METHODS = [
        ('CASH', 'Cash'),
        ('CARD', 'Credit/Debit Card'),
        ('MOBILE_MONEY', 'Mobile Money'),
        ('INSURANCE', 'Insurance'),
        ('CREDIT', 'Credit'),
        ('SPLIT', 'Split Payment'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('REFUNDED', 'Refunded'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Transaction Details
    receipt_number = models.CharField(max_length=50, unique=True, editable=False)
    date = models.DateTimeField(default=timezone.now)
    
    # Customer Information
    customer = models.ForeignKey(Patient, on_delete=models.SET_NULL, null=True, blank=True, related_name='pharmacy_pos_transactions')
    customer_name = models.CharField(max_length=200, blank=True, help_text="For walk-in customers")
    customer_phone = models.CharField(max_length=20, blank=True)
    
    # Prescription Reference
    prescription = models.ForeignKey(Prescription, on_delete=models.SET_NULL, null=True, blank=True, related_name='pos_sales')
    
    # Financial Details
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    # Payment Details
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='CASH')
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    change_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # Insurance Details
    insurance_claim_number = models.CharField(max_length=100, blank=True)
    insurance_coverage_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(0)])
    
    # Status and Notes
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    notes = models.TextField(blank=True)
    
    # Staff and Tracking
    cashier = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='pharmacy_transactions')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Pharmacy PoS Transaction')
        verbose_name_plural = _('Pharmacy PoS Transactions')
    
    def save(self, *args, **kwargs):
        if not self.receipt_number:
            self.receipt_number = self.generate_receipt_number()
        super().save(*args, **kwargs)
    
    def generate_receipt_number(self):
        """Generate unique receipt number"""
        import random
        import string
        today = timezone.now()
        prefix = f"PH{today.strftime('%Y%m%d')}"
        suffix = ''.join(random.choices(string.digits, k=4))
        return f"{prefix}{suffix}"
    
    def __str__(self):
        return f"Receipt {self.receipt_number} - ${self.total_amount}"
    
    def get_customer_name(self):
        """Get customer name (either from patient or walk-in)"""
        if self.customer:
            return self.customer.get_full_name()
        return self.customer_name or "Walk-in Customer"


class PharmacyPoSTransactionItem(models.Model):
    """Items in a pharmacy PoS transaction"""
    
    transaction = models.ForeignKey(PharmacyPoSTransaction, on_delete=models.CASCADE, related_name='items')
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    
    # Quantity and Pricing
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(0)])
    
    # Calculated fields
    line_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    # Prescription Item Reference
    prescription_item = models.ForeignKey(PrescriptionItem, on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
        verbose_name = _('Pharmacy PoS Transaction Item')
        verbose_name_plural = _('Pharmacy PoS Transaction Items')
    
    def save(self, *args, **kwargs):
        # Calculate line total
        subtotal = self.quantity * self.unit_price
        discount_amount = subtotal * (self.discount_percentage / 100)
        self.line_total = subtotal - discount_amount
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.medicine.name} x {self.quantity}"


class PharmacyPoSPayment(models.Model):
    """Payment details for split payments in pharmacy PoS"""
    
    PAYMENT_METHODS = [
        ('CASH', 'Cash'),
        ('CARD', 'Credit/Debit Card'),
        ('MOBILE_MONEY', 'Mobile Money'),
        ('INSURANCE', 'Insurance'),
    ]
    
    transaction = models.ForeignKey(PharmacyPoSTransaction, on_delete=models.CASCADE, related_name='payments')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    
    # Payment Method Specific Details
    card_last_four = models.CharField(max_length=4, blank=True, help_text="Last 4 digits of card")
    card_type = models.CharField(max_length=20, blank=True, help_text="Visa, Mastercard, etc.")
    mobile_money_number = models.CharField(max_length=20, blank=True)
    mobile_money_provider = models.CharField(max_length=50, blank=True)
    
    # Insurance Details
    insurance_provider = models.CharField(max_length=100, blank=True)
    insurance_policy_number = models.CharField(max_length=100, blank=True)
    
    reference_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
        verbose_name = _('Pharmacy PoS Payment')
        verbose_name_plural = _('Pharmacy PoS Payments')
    
    def __str__(self):
        return f"{self.get_payment_method_display()} - ${self.amount}"


class PharmacyPoSDayClose(models.Model):
    """Daily closing records for pharmacy PoS"""
    
    date = models.DateField()
    cashier = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pharmacy_day_closes')
    
    # Transaction Counts
    total_transactions = models.PositiveIntegerField(default=0)
    completed_transactions = models.PositiveIntegerField(default=0)
    cancelled_transactions = models.PositiveIntegerField(default=0)
    refunded_transactions = models.PositiveIntegerField(default=0)
    
    # Financial Summary
    gross_sales = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_discounts = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_tax = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    net_sales = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    # Payment Method Breakdown
    cash_sales = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    card_sales = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    mobile_money_sales = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    insurance_sales = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    credit_sales = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    # Cash Management
    opening_cash = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    closing_cash_expected = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    closing_cash_actual = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    cash_variance = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    notes = models.TextField(blank=True)
    is_closed = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-date']
        unique_together = ['date', 'cashier']
        verbose_name = _('Pharmacy PoS Day Close')
        verbose_name_plural = _('Pharmacy PoS Day Closes')
    
    def __str__(self):
        return f"Day Close {self.date} - {self.cashier.get_full_name()}"


# Enhanced Pharmacy Bill Model for better integration with PoS
class PharmacyBill(models.Model):
    """Pharmacy bills for prescription fulfillment and PoS integration"""
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PARTIAL', 'Partially Paid'),
        ('PAID', 'Fully Paid'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bill_number = models.CharField(max_length=50, unique=True, editable=False)
    
    # References
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='pharmacy_bills')
    prescription = models.ForeignKey(Prescription, on_delete=models.SET_NULL, null=True, blank=True, related_name='bills')
    pos_transaction = models.OneToOneField(PharmacyPoSTransaction, on_delete=models.SET_NULL, null=True, blank=True, related_name='bill')
    
    # Financial Details
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    # Status and Metadata
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    notes = models.TextField(blank=True)
    
    # Staff and Tracking
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_pharmacy_bills')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Pharmacy Bill')
        verbose_name_plural = _('Pharmacy Bills')
    
    def save(self, *args, **kwargs):
        if not self.bill_number:
            self.bill_number = self.generate_bill_number()
        super().save(*args, **kwargs)
    
    def generate_bill_number(self):
        """Generate unique bill number"""
        import random
        import string
        today = timezone.now()
        prefix = f"PB{today.strftime('%Y%m%d')}"
        suffix = ''.join(random.choices(string.digits, k=4))
        return f"{prefix}{suffix}"
    
    def __str__(self):
        return f"Bill {self.bill_number} - {self.patient.get_full_name()}"
    
    @property
    def balance_due(self):
        """Calculate remaining balance"""
        return self.total_amount - self.paid_amount

