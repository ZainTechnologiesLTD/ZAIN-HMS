# apps/billing/forms.py
from django import forms
from django.utils import timezone
from datetime import timedelta
from .models import Invoice, MedicalService
from apps.patients.models import Patient
from apps.appointments.models import Appointment


class BillCreateForm(forms.ModelForm):
    """Form for creating new bills/invoices"""
    
    class Meta:
        model = Invoice
        fields = [
            'patient', 'appointment', 'invoice_date', 'due_date', 
            'payment_terms', 'notes', 'discount_percentage'
        ]
        widgets = {
            'patient': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'appointment': forms.Select(attrs={
                'class': 'form-select'
            }),
            'invoice_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'value': timezone.now().date()
            }),
            'due_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'value': (timezone.now().date() + timedelta(days=30))
            }),
            'payment_terms': forms.Select(attrs={
                'class': 'form-select'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter any additional notes...'
            }),
            'discount_percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'value': '0.00'
            })
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user and hasattr(user, 'hospital'):
            # Filter patients and appointments by hospital
            patient_queryset = Patient.objects.filter(
                hospital=user.hospital
            ).order_by('last_name', 'first_name')
            
            self.fields['appointment'].queryset = Appointment.objects.filter(
                hospital=user.hospital,
                status='COMPLETED'
            ).order_by('-appointment_date')
        else:
            # Fallback to all patients/appointments
            patient_queryset = Patient.objects.all().order_by('last_name', 'first_name')
            self.fields['appointment'].queryset = Appointment.objects.filter(
                status='COMPLETED'
            ).order_by('-appointment_date')
        
        # Set patient queryset
        self.fields['patient'].queryset = patient_queryset
        
        # Update patient choice labels to show full names
        patient_choices = [(None, "Select a patient")]
        for patient in patient_queryset:
            patient_choices.append((patient.pk, patient.get_full_name()))
        
        self.fields['patient'].choices = patient_choices
        
        # Make appointment field optional
        self.fields['appointment'].required = False
        self.fields['appointment'].empty_label = "No appointment (Direct billing)"

    def clean(self):
        cleaned_data = super().clean()
        invoice_date = cleaned_data.get('invoice_date')
        due_date = cleaned_data.get('due_date')
        
        if invoice_date and due_date:
            if due_date < invoice_date:
                raise forms.ValidationError("Due date cannot be earlier than invoice date.")
        
        return cleaned_data


class InvoiceItemForm(forms.Form):
    """Form for adding individual services/items to an invoice"""
    
    service = forms.ModelChoiceField(
        queryset=MedicalService.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="Select a service"
    )
    
    quantity = forms.IntegerField(
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1'
        })
    )
    
    unit_price = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0'
        })
    )
    
    description = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Optional description'
        })
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user and hasattr(user, 'hospital'):
            self.fields['service'].queryset = MedicalService.objects.filter(
                hospital=user.hospital,
                is_active=True
            ).order_by('name')
