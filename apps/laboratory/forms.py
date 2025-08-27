# apps/laboratory/forms.py
from django import forms
from django.utils import timezone
from .models import LabTest, LabOrder, LabOrderItem, LabResult, TestCategory
from apps.patients.models import Patient
from apps.doctors.models import Doctor


class LabTestForm(forms.ModelForm):
    """Form for creating/editing lab tests"""
    
    class Meta:
        model = LabTest
        fields = [
            'name', 'description', 'category', 'sample_type', 'sample_volume',
            'collection_instructions', 'price', 'reporting_time_hours',
            'reference_range_male', 'reference_range_female', 'reference_range_child',
            'units', 'requires_fasting', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter test name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter test description'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'sample_type': forms.Select(attrs={'class': 'form-control'}),
            'sample_volume': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 5ml blood'}),
            'collection_instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'reporting_time_hours': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'reference_range_male': forms.TextInput(attrs={'class': 'form-control'}),
            'reference_range_female': forms.TextInput(attrs={'class': 'form-control'}),
            'reference_range_child': forms.TextInput(attrs={'class': 'form-control'}),
            'units': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., mg/dL, %'}),
            'requires_fasting': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        # Handle both 'tenant' and 'hospital' parameters for backward compatibility
        tenant = kwargs.pop('tenant', None)
        hospital = kwargs.pop('hospital', None)
        
        # Use tenant if provided, otherwise fall back to hospital
        filter_param = tenant or hospital
        
        super().__init__(*args, **kwargs)
        
        if filter_param:
            self.fields['category'].queryset = TestCategory.objects.filter(
                hospital=filter_param, is_active=True
            )
        else:
            # No tenant/hospital provided - set empty queryset using default database to prevent routing errors
            self.fields['category'].queryset = TestCategory.objects.using('default').none()


class TestCategoryForm(forms.ModelForm):
    """Form for creating/editing test categories"""
    
    class Meta:
        model = TestCategory
        fields = ['name', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter category name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class LabOrderForm(forms.ModelForm):
    """Form for creating lab orders"""
    
    class Meta:
        model = LabOrder
        fields = [
            'patient', 'doctor', 'priority', 'clinical_history',
            'provisional_diagnosis', 'special_instructions'
        ]
        widgets = {
            'patient': forms.Select(attrs={'class': 'form-control'}),
            'doctor': forms.Select(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'clinical_history': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'provisional_diagnosis': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'special_instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        # Handle both 'tenant' and 'hospital' parameters for backward compatibility
        tenant = kwargs.pop('tenant', None)
        hospital = kwargs.pop('hospital', None)
        
        # Use tenant if provided, otherwise fall back to hospital
        filter_param = tenant or hospital
        
        super().__init__(*args, **kwargs)
        
        if filter_param:
            self.fields['patient'].queryset = Patient.objects.filter(hospital=filter_param)
            
            # Avoid cross-database queries for Doctor filtering
            from apps.accounts.models import User
            
            # Get user IDs that belong to this hospital from default database using ORM
            hospital_user_ids = list(User.objects.using('default').filter(
                hospital=filter_param
            ).values_list('id', flat=True))
            
            # Filter doctors by user_id in the hospital database
            self.fields['doctor'].queryset = Doctor.objects.filter(user_id__in=hospital_user_ids)
        else:
            # No tenant/hospital provided - set empty querysets using default database to prevent routing errors
            self.fields['patient'].queryset = Patient.objects.using('default').none()
            self.fields['doctor'].queryset = Doctor.objects.using('default').none()


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
        
        if hospital:
            self.fields['test'].queryset = LabTest.objects.filter(
                hospital=hospital, is_active=True
            ).order_by('name')


class LabResultForm(forms.ModelForm):
    """Form for entering lab results"""
    
    class Meta:
        model = LabResult
        fields = [
            'result_value', 'result_unit', 'reference_range', 'is_abnormal',
            'abnormal_flag', 'methodology', 'comments', 'interpretation',
            'result_file'
        ]
        widgets = {
            'result_value': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'result_unit': forms.TextInput(attrs={'class': 'form-control'}),
            'reference_range': forms.TextInput(attrs={'class': 'form-control'}),
            'is_abnormal': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'abnormal_flag': forms.Select(attrs={'class': 'form-control'}, choices=[
                ('', 'Normal'),
                ('H', 'High'),
                ('L', 'Low'),
                ('HH', 'Very High'),
                ('LL', 'Very Low'),
            ]),
            'methodology': forms.TextInput(attrs={'class': 'form-control'}),
            'comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'interpretation': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'result_file': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        # Remove tenant parameter if provided (not used in this form)
        kwargs.pop('tenant', None)
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
