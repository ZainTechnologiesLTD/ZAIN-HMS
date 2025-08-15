# apps/billing/models.py
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal
from apps.accounts.models import Hospital, User
from apps.patients.models import Patient
from apps.appointments.models import Appointment
import uuid

class ServiceCategory(models.Model):
    """Categories for medical services"""
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='service_categories')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['hospital', 'name']
        ordering = ['name']
        verbose_name_plural = "Service Categories"
    
    def __str__(self):
        return self.name


class MedicalService(models.Model):
    """Medical services and their pricing"""
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='medical_services')
    category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE, related_name='services')
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    duration_minutes = models.PositiveIntegerField(default=30)
    is_taxable = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['hospital', 'code']
        ordering = ['name']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class Invoice(models.Model):
    """Main invoice/bill model"""
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PENDING', 'Pending'),
        ('PARTIALLY_PAID', 'Partially Paid'),
        ('PAID', 'Paid'),
        ('OVERDUE', 'Overdue'),
        ('CANCELLED', 'Cancelled'),
        ('REFUNDED', 'Refunded'),
    ]
    
    PAYMENT_TERMS = [
        ('IMMEDIATE', 'Immediate'),
        ('NET_15', 'Net 15 Days'),
        ('NET_30', 'Net 30 Days'),
    ]
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='invoices')
    invoice_number = models.CharField(max_length=20, unique=True, blank=True)
    
    # Patient Information
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='invoices')
    appointment = models.ForeignKey(Appointment, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Invoice Details
    invoice_date = models.DateField(default=timezone.now)
    due_date = models.DateField()
    payment_terms = models.CharField(max_length=20, choices=PAYMENT_TERMS, default='IMMEDIATE')
    
    # Amounts
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    balance_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    
    # Notes
    notes = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True)
    
    # Tracking
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_invoices')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Payment Information
    last_payment_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['invoice_number']),
            models.Index(fields=['status']),
            models.Index(fields=['due_date']),
            models.Index(fields=['patient']),
        ]
    
    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.patient.get_full_name()}"
    
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = self.generate_invoice_number()
        
        # Calculate totals
        self.calculate_totals()
        
        # Update status based on payments
        self.update_status()
        
        super().save(*args, **kwargs)
    
    def generate_invoice_number(self):
        """Generate unique invoice number"""
        from datetime import datetime
        
        today = datetime.now()
        date_str = today.strftime('%Y%m%d')
        
        last_invoice = Invoice.objects.filter(
            hospital=self.hospital,
            created_at__date=today.date()
        ).order_by('-created_at').first()
        
        if last_invoice and last_invoice.invoice_number:
            try:
                last_number = int(last_invoice.invoice_number.split('-')[-1])
                new_number = last_number + 1
            except:
                new_number = 1
        else:
            new_number = 1
            
        return f"{self.hospital.code}-INV-{date_str}-{new_number:04d}"
    
    def calculate_totals(self):
        """Calculate invoice totals"""
        self.subtotal = sum(item.total_amount for item in self.items.all())
        
        # Calculate discount
        if self.discount_percentage > 0:
            self.discount_amount = (self.subtotal * self.discount_percentage) / 100
        
        # Calculate tax on discounted amount
        taxable_amount = self.subtotal - self.discount_amount
        if self.tax_rate > 0:
            self.tax_amount = (taxable_amount * self.tax_rate) / 100
        
        # Calculate total
        self.total_amount = self.subtotal - self.discount_amount + self.tax_amount
        
        # Calculate balance
        self.balance_amount = self.total_amount - self.paid_amount
    
    def update_status(self):
        """Update invoice status based on payments"""
        if self.paid_amount <= 0:
            if self.due_date < timezone.now().date() and self.status == 'PENDING':
                self.status = 'OVERDUE'
            elif self.status not in ['DRAFT', 'CANCELLED', 'REFUNDED']:
                self.status = 'PENDING'
        elif self.paid_amount >= self.total_amount:
            self.status = 'PAID'
        else:
            self.status = 'PARTIALLY_PAID'
    
    def get_status_color(self):
        """Return Bootstrap color class for status"""
        colors = {
            'DRAFT': 'secondary',
            'PENDING': 'warning',
            'PARTIALLY_PAID': 'info',
            'PAID': 'success',
            'OVERDUE': 'danger',
            'CANCELLED': 'dark',
            'REFUNDED': 'primary',
        }
        return colors.get(self.status, 'secondary')


class InvoiceItem(models.Model):
    """Individual items on an invoice"""
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    service = models.ForeignKey(MedicalService, on_delete=models.CASCADE)
    description = models.CharField(max_length=500)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        ordering = ['id']
    
    def save(self, *args, **kwargs):
        self.total_amount = self.quantity * self.unit_price
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.description} - {self.quantity} x {self.unit_price}"


class Payment(models.Model):
    """Payment records for invoices"""
    PAYMENT_METHODS = [
        ('CASH', 'Cash'),
        ('CREDIT_CARD', 'Credit Card'),
        ('DEBIT_CARD', 'Debit Card'),
        ('CHECK', 'Check'),
        ('BANK_TRANSFER', 'Bank Transfer'),
        ('INSURANCE', 'Insurance'),
        ('ONLINE', 'Online Payment'),
        ('OTHER', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
        ('REFUNDED', 'Refunded'),
    ]
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    payment_number = models.CharField(max_length=20, unique=True, blank=True)
    
    # Payment Details
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    payment_date = models.DateTimeField(default=timezone.now)
    
    # Transaction Details
    transaction_id = models.CharField(max_length=100, blank=True)
    reference_number = models.CharField(max_length=100, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='COMPLETED')
    
    # Notes
    notes = models.TextField(blank=True)
    
    # Tracking
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='processed_payments')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"Payment {self.payment_number} - {self.amount}"
    
    def save(self, *args, **kwargs):
        if not self.payment_number:
            self.payment_number = self.generate_payment_number()
        super().save(*args, **kwargs)
        
        # Update invoice paid amount
        self.update_invoice_payment()
    
    def generate_payment_number(self):
        """Generate unique payment number"""
        from datetime import datetime
        
        today = datetime.now()
        date_str = today.strftime('%Y%m%d')
        
        last_payment = Payment.objects.filter(
            created_at__date=today.date()
        ).order_by('-created_at').first()
        
        if last_payment and last_payment.payment_number:
            try:
                last_number = int(last_payment.payment_number.split('-')[-1])
                new_number = last_number + 1
            except:
                new_number = 1
        else:
            new_number = 1
            
        return f"PAY-{date_str}-{new_number:06d}"
    
    def update_invoice_payment(self):
        """Update invoice payment totals"""
        if self.status == 'COMPLETED':
            total_paid = self.invoice.payments.filter(status='COMPLETED').aggregate(
                total=models.Sum('amount')
            )['total'] or Decimal('0.00')
            
            self.invoice.paid_amount = total_paid
            self.invoice.last_payment_date = timezone.now()
            self.invoice.save(update_fields=['paid_amount', 'last_payment_date'])


class InsuranceClaim(models.Model):
    """Insurance claims for invoices"""
    STATUS_CHOICES = [
        ('SUBMITTED', 'Submitted'),
        ('UNDER_REVIEW', 'Under Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('PAID', 'Paid'),
    ]
    
    invoice = models.OneToOneField(Invoice, on_delete=models.CASCADE, related_name='insurance_claim')
    claim_number = models.CharField(max_length=50, unique=True, blank=True)
    
    # Insurance Details
    insurance_provider = models.CharField(max_length=200)
    policy_number = models.CharField(max_length=100)
    group_number = models.CharField(max_length=100, blank=True)
    
    # Claim Details
    claim_amount = models.DecimalField(max_digits=10, decimal_places=2)
    approved_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    deductible_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # Status and Dates
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SUBMITTED')
    submitted_date = models.DateField(auto_now_add=True)
    response_date = models.DateField(null=True, blank=True)
    
    # Notes
    notes = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)
    
    # Tracking
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Claim {self.claim_number} - {self.insurance_provider}"
    
    def save(self, *args, **kwargs):
        if not self.claim_number:
            self.claim_number = self.generate_claim_number()
        super().save(*args, **kwargs)
    
    def generate_claim_number(self):
        """Generate unique claim number"""
        from datetime import datetime
        
        today = datetime.now()
        date_str = today.strftime('%Y%m%d')
        
        last_claim = InsuranceClaim.objects.filter(
            created_at__date=today.date()
        ).order_by('-created_at').first()
        
        if last_claim and last_claim.claim_number:
            try:
                last_number = int(last_claim.claim_number.split('-')[-1])
                new_number = last_number + 1
            except:
                new_number = 1
        else:
            new_number = 1
            
        return f"CLM-{date_str}-{new_number:05d}"