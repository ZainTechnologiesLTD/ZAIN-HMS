# apps/billing/pos_forms.py
from django import forms
from django.core.exceptions import ValidationError
from decimal import Decimal
from .models import (
    PoSCategory, PoSItem, PoSTransaction, PoSTransactionItem, PoSDayClose
)
from apps.patients.models import Patient


class PoSCategoryForm(forms.ModelForm):
    """Form for creating/editing PoS categories"""
    
    class Meta:
        model = PoSCategory
        fields = ['name', 'description', 'icon', 'color', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Category name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Category description'
            }),
            'icon': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'fas fa-pills (Font Awesome icon class)'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color',
                'title': 'Choose category color'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }


class PoSItemForm(forms.ModelForm):
    """Form for creating/editing PoS items"""
    
    class Meta:
        model = PoSItem
        fields = [
            'category', 'item_code', 'name', 'description', 'item_type',
            'cost_price', 'selling_price', 'discount_price',
            'current_stock', 'minimum_stock', 'maximum_stock',
            'is_taxable', 'tax_rate', 'is_prescription_required',
            'barcode', 'manufacturer', 'batch_number', 'expiry_date', 'is_active'
        ]
        widgets = {
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'item_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Item code (auto-generated if empty)'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Item name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Item description'
            }),
            'item_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'cost_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'selling_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'discount_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'current_stock': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'minimum_stock': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'maximum_stock': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),
            'is_taxable': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'tax_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100'
            }),
            'is_prescription_required': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'barcode': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Barcode (optional)'
            }),
            'manufacturer': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Manufacturer name'
            }),
            'batch_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Batch number'
            }),
            'expiry_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def clean(self):
        cleaned_data = super().clean()
        cost_price = cleaned_data.get('cost_price')
        selling_price = cleaned_data.get('selling_price')
        discount_price = cleaned_data.get('discount_price')
        minimum_stock = cleaned_data.get('minimum_stock')
        maximum_stock = cleaned_data.get('maximum_stock')
        
        # Validate pricing
        if cost_price and selling_price and cost_price >= selling_price:
            raise ValidationError('Selling price must be greater than cost price.')
        
        if discount_price and selling_price and discount_price >= selling_price:
            raise ValidationError('Discount price must be less than selling price.')
        
        # Validate stock levels
        if minimum_stock and maximum_stock and minimum_stock >= maximum_stock:
            raise ValidationError('Maximum stock must be greater than minimum stock.')
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Auto-generate item code if not provided
        if not instance.item_code:
            # Generate code based on category and name
            category_code = instance.category.name[:3].upper()
            name_code = ''.join([word[:2].upper() for word in instance.name.split()[:2]])
            
            # Find next available number
            base_code = f"{category_code}-{name_code}"
            counter = 1
            while PoSItem.objects.filter(item_code=f"{base_code}-{counter:03d}").exists():
                counter += 1
            
            instance.item_code = f"{base_code}-{counter:03d}"
        
        if commit:
            instance.save()
        return instance


class PoSTransactionForm(forms.ModelForm):
    """Form for creating PoS transactions"""
    
    patient_search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search patient by name, phone, or ID',
            'data-toggle': 'patient-search'
        })
    )
    
    class Meta:
        model = PoSTransaction
        fields = [
            'patient', 'customer_name', 'customer_phone', 
            'payment_method', 'amount_received', 'discount_amount', 'notes'
        ]
        widgets = {
            'patient': forms.HiddenInput(),
            'customer_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Customer name (for non-patients)'
            }),
            'customer_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Customer phone'
            }),
            'payment_method': forms.Select(attrs={
                'class': 'form-control'
            }),
            'amount_received': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'discount_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Transaction notes'
            })
        }


class PoSStockUpdateForm(forms.Form):
    """Form for updating stock levels"""
    
    STOCK_ACTIONS = [
        ('ADD', 'Add Stock'),
        ('REMOVE', 'Remove Stock'),
        ('SET', 'Set Stock Level'),
    ]
    
    action = forms.ChoiceField(
        choices=STOCK_ACTIONS,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    quantity = forms.IntegerField(
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0'
        })
    )
    
    reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Reason for stock adjustment'
        })
    )
    
    def __init__(self, item, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.item = item
        self.fields['quantity'].help_text = f'Current stock: {item.current_stock}'
    
    def clean_quantity(self):
        quantity = self.cleaned_data['quantity']
        action = self.cleaned_data.get('action')
        
        if action == 'REMOVE' and quantity > self.item.current_stock:
            raise ValidationError(
                f'Cannot remove {quantity} items. Current stock: {self.item.current_stock}'
            )
        
        return quantity


class PoSDayCloseForm(forms.ModelForm):
    """Form for closing the day"""
    
    class Meta:
        model = PoSDayClose
        fields = ['opening_cash', 'closing_cash', 'notes']
        widgets = {
            'opening_cash': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'closing_cash': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Any notes about the day closing'
            })
        }


class PoSReportFilterForm(forms.Form):
    """Form for filtering PoS reports"""
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    payment_method = forms.ChoiceField(
        choices=[('', 'All Payment Methods')] + PoSTransaction.PAYMENT_METHODS,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    cashier = forms.ModelChoiceField(
        queryset=None,  # Will be set in __init__
        required=False,
        empty_label="All Cashiers",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    category = forms.ModelChoiceField(
        queryset=PoSCategory.objects.filter(is_active=True),
        required=False,
        empty_label="All Categories",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set cashier queryset
        from apps.accounts.models import CustomUser as User
        self.fields['cashier'].queryset = User.objects.filter(
            pos_transactions__isnull=False
        ).distinct().order_by('first_name', 'last_name')
