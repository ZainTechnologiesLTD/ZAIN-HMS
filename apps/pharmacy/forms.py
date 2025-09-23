# apps/pharmacy/forms.py
from django import forms
from django.db.models import Sum, Q
from decimal import Decimal

from .models import (
    Medicine, PharmacySale, PharmacySaleItem, MedicineStock, 
    DrugCategory, Manufacturer, Prescription
)


class MedicineForm(forms.ModelForm):
    """Form for adding/editing medicines."""
    
    class Meta:
        model = Medicine
        fields = [
            'generic_name', 'brand_name', 'category', 'manufacturer',
            'dosage_form', 'strength', 'cost_price', 'selling_price', 'mrp',
            'current_stock', 'reorder_level', 'maximum_stock', 'is_active'
        ]
        widgets = {
            'generic_name': forms.TextInput(attrs={'class': 'form-control'}),
            'brand_name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'manufacturer': forms.Select(attrs={'class': 'form-control'}),
            'dosage_form': forms.Select(attrs={'class': 'form-control'}),
            'strength': forms.TextInput(attrs={'class': 'form-control'}),
            'cost_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'selling_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'mrp': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'current_stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'reorder_level': forms.NumberInput(attrs={'class': 'form-control'}),
            'maximum_stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class MedicineSearchForm(forms.Form):
    """Form for searching medicines."""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by medicine name or code...'
        })
    )
    category = forms.ModelChoiceField(
        queryset=DrugCategory.objects.filter(is_active=True),
        required=False,
        empty_label="All Categories",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    manufacturer = forms.ModelChoiceField(
        queryset=Manufacturer.objects.filter(is_active=True),
        required=False,
        empty_label="All Manufacturers",
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class PharmacySaleForm(forms.ModelForm):
    """Form for creating pharmacy sales."""
    
    class Meta:
        model = PharmacySale
        fields = [
            'customer_name', 'customer_phone', 'discount_amount', 'payment_method'
        ]
        widgets = {
            'customer_name': forms.TextInput(attrs={'class': 'form-control'}),
            'customer_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'discount_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
        }


class PharmacySaleItemForm(forms.ModelForm):
    """Form for adding items to pharmacy sale."""
    
    medicine = forms.ModelChoiceField(
        queryset=Medicine.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-control medicine-select'})
    )
    
    class Meta:
        model = PharmacySaleItem
        fields = ['medicine', 'quantity', 'unit_price']
        widgets = {
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add stock information to medicine choices
        medicines = Medicine.objects.filter(is_active=True)
        choices = []
        for medicine in medicines:
            stock = medicine.current_stock or 0
            choice_text = f"{medicine.generic_name} - {medicine.brand_name} (Stock: {stock})"
            choices.append((medicine.id, choice_text))
        
        self.fields['medicine'].choices = choices


class MedicineStockForm(forms.ModelForm):
    """Form for managing medicine stock."""
    
    class Meta:
        model = MedicineStock
        fields = [
            'medicine', 'transaction_type', 'quantity', 'unit_cost', 'reference_number', 'notes'
        ]
        widgets = {
            'medicine': forms.Select(attrs={'class': 'form-control'}),
            'transaction_type': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'unit_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'reference_number': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class PrescriptionForm(forms.ModelForm):
    """Form for creating prescriptions."""
    
    class Meta:
        model = Prescription
        fields = ['patient', 'doctor', 'diagnosis', 'notes']
        widgets = {
            'patient': forms.Select(attrs={'class': 'form-control'}),
            'doctor': forms.Select(attrs={'class': 'form-control'}),
            'diagnosis': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class DrugCategoryForm(forms.ModelForm):
    """Form for managing drug categories."""
    
    class Meta:
        model = DrugCategory
        fields = ['name', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class ManufacturerForm(forms.ModelForm):
    """Form for managing manufacturers."""
    
    class Meta:
        model = Manufacturer
        fields = [
            'name', 'code', 'contact_person', 'phone', 
            'email', 'address', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class StockAlertForm(forms.Form):
    """Form for setting up stock alerts."""
    
    ALERT_TYPES = [
        ('low_stock', 'Low Stock Alert'),
        ('expired', 'Expired Medicine Alert'),
        ('expiring_soon', 'Expiring Soon Alert'),
    ]
    
    alert_type = forms.ChoiceField(
        choices=ALERT_TYPES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    threshold_days = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text="Days before expiry to send alert (for expiring soon alerts)"
    )
    email_recipients = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text="Comma-separated email addresses"
    )


# Formsets for handling multiple items
PharmacySaleItemFormSet = forms.inlineformset_factory(
    PharmacySale, 
    PharmacySaleItem, 
    form=PharmacySaleItemForm,
    extra=1,
    can_delete=True
)


class MedicineSearchForm(forms.Form):
    """Form for searching medicines"""
    search = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search medicines by name, code, or brand...'
        })
    )
    
    category = forms.ModelChoiceField(
        queryset=DrugCategory.objects.filter(is_active=True),
        required=False,
        empty_label='All Categories',
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    manufacturer = forms.ModelChoiceField(
        queryset=Manufacturer.objects.filter(is_active=True),
        required=False,
        empty_label='All Manufacturers',
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
