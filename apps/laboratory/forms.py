# apps/laboratory/forms.py
from django import forms
from django.utils import timezone
from .models import LabTest, LabOrder, LabOrderItem, LabReport, LabSection
from apps.patients.models import Patient
from apps.doctors.models import Doctor


class LabTestForm(forms.ModelForm):
    """Form for creating/editing lab tests"""
    
    class Meta:
        model = LabTest
        fields = [
            'name', 'code', 'description', 'section', 'cost_price', 'selling_price',
            'normal_range', 'normal_range_child', 'unit', 
            'sample_collection_time', 'processing_time', 'requires_fasting', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter test name'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter test code'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter test description'}),
            'section': forms.Select(attrs={'class': 'form-control'}),
            'cost_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'selling_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'normal_range': forms.TextInput(attrs={'class': 'form-control'}),
            'normal_range_child': forms.TextInput(attrs={'class': 'form-control'}),
            'unit': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., mg/dL, %'}),
            'requires_fasting': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['section'].queryset = LabSection.objects.filter(is_active=True)


class LabSectionForm(forms.ModelForm):
    """Form for creating/editing lab sections"""
    
    class Meta:
        model = LabSection
        fields = ['name', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter section name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class LabOrderForm(forms.ModelForm):
    """Form for creating lab orders"""
    
    class Meta:
        model = LabOrder
        fields = [
            'patient', 'doctor', 'priority', 'clinical_history', 'special_instructions'
        ]
        widgets = {
            'patient': forms.Select(attrs={'class': 'form-control'}),
            'doctor': forms.Select(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'clinical_history': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'special_instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        # Handle both 'tenant' and 'hospital' parameters for backward compatibility
        super().__init__(*args, **kwargs)
        
        self.fields['patient'].queryset = Patient.objects.all()
        self.fields['doctor'].queryset = Doctor.objects.all()


class LabOrderItemForm(forms.Form):
    """Form for selecting tests in lab order"""
    test = forms.ModelChoiceField(
        queryset=LabTest.objects.none(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Select a test"
    )
    
    def __init__(self, *args, **kwargs):
        hospital = kwargs.pop('hospital', None)
        super().__init__(*args, **kwargs)
        
        if True:  # Unified ZAIN HMS system
            self.fields['test'].queryset = LabTest.objects.filter(
                hospital=hospital, is_active=True
            ).order_by('name')


class LabResultForm(forms.ModelForm):
    """Form for entering lab results"""
    
    class Meta:
        model = LabReport
        fields = [
            'clinical_findings', 'interpretation', 'recommendations', 'delivery_method'
        ]
        widgets = {
            'clinical_findings': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'interpretation': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'recommendations': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'delivery_method': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Pre-fill reference range from test definition if available
        if self.instance and self.instance.order_item:
            test = self.instance.order_item.test
            if not self.instance.reference_range and test.reference_range_male:
                self.fields['reference_range'].initial = test.reference_range_male
            if not self.instance.result_unit and test.units:
                self.fields['result_unit'].initial = test.units


class SampleCollectionForm(forms.ModelForm):
    """Form for recording sample collection"""
    
    class Meta:
        model = LabOrder
        fields = ['sample_collected_at']
        widgets = {
            'sample_collected_at': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default to current time
        if not self.instance.sample_collected_at:
            self.fields['sample_collected_at'].initial = timezone.now().strftime('%Y-%m-%dT%H:%M')
