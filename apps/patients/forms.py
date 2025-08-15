# apps/patients/forms.py
from django import forms
from .models import Patient, PatientDocument, PatientNote, PatientVitals

class PatientForm(forms.ModelForm):
    """Main patient registration/update form"""
    Assistant
    class Meta:
        model = Patient
        fields = [
            'first_name', 'middle_name', 'last_name', 'date_of_birth',
            'gender', 'blood_group', 'marital_status', 'phone', 'alternate_phone',
            'email', 'address_line1', 'address_line2', 'city', 'state',
            'postal_code', 'country', 'emergency_contact_name',
            'emergency_contact_relationship', 'emergency_contact_phone',
            'allergies', 'chronic_conditions', 'current_medications',
            'medical_history', 'family_medical_history', 'insurance_provider',
            'insurance_policy_number', 'insurance_group_number',
            'profile_picture', 'is_vip', 'notes'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'blood_group': forms.Select(attrs={'class': 'form-select'}),
            'marital_status': forms.Select(attrs={'class': 'form-select'}),
            'allergies': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'chronic_conditions': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'current_medications': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'medical_history': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'family_medical_history': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'is_vip': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add form-control class to all fields except specific ones
        for field_name, field in self.fields.items():
            if field_name not in ['gender', 'blood_group', 'marital_status', 'is_vip', 'profile_picture']:
                field.widget.attrs['class'] = 'form-control'
            
            # Make certain fields required
            if field_name in ['first_name', 'last_name', 'date_of_birth', 'gender', 'phone', 
                            'address_line1', 'city', 'state', 'postal_code', 
                            'emergency_contact_name', 'emergency_contact_phone']:
                field.required = True


class QuickPatientForm(forms.ModelForm):
    """Quick patient registration form with essential fields only"""
    
    class Meta:
        model = Patient
        fields = [
            'first_name', 'last_name', 'date_of_birth', 'gender',
            'phone', 'email', 'address_line1', 'city'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name not in ['gender']:
                field.widget.attrs['class'] = 'form-control'
            field.required = True


class PatientSearchForm(forms.Form):
    """Patient search form"""
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by name, patient ID, or phone...',
            'autocomplete': 'off'
        })
    )
    gender = forms.ChoiceField(
        choices=[('', 'All Genders')] + Patient.GENDER_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    blood_group = forms.ChoiceField(
        choices=[('', 'All Blood Groups')] + Patient.BLOOD_GROUP_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    is_vip = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class PatientDocumentForm(forms.ModelForm):
    """Form for uploading patient documents"""
    
    class Meta:
        model = PatientDocument
        fields = ['document_type', 'title', 'description', 'file', 'is_confidential']
        widgets = {
            'document_type': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'is_confidential': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class PatientNoteForm(forms.ModelForm):
    """Form for adding patient notes"""
    
    class Meta:
        model = PatientNote
        fields = ['note', 'is_private']
        widgets = {
            'note': forms.Textarea(attrs={'rows': 4, 'class': 'form-control', 'placeholder': 'Enter note...'}),
            'is_private': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class PatientVitalsForm(forms.ModelForm):
    """Form for recording patient vitals"""
    
    class Meta:
        model = PatientVitals
        fields = [
            'temperature', 'blood_pressure_systolic', 'blood_pressure_diastolic',
            'heart_rate', 'respiratory_rate', 'oxygen_saturation',
            'weight', 'height', 'notes'
        ]
        widgets = {
            'temperature': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'placeholder': '98.6'}),
            'blood_pressure_systolic': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '120'}),
            'blood_pressure_diastolic': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '80'}),
            'heart_rate': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '72'}),
            'respiratory_rate': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '16'}),
            'oxygen_saturation': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '98'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '70.0'}),
            'height': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '170.0'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
