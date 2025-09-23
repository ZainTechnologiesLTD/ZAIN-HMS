# apps/patients/forms.py
from django import forms
from django.core.exceptions import ValidationError
from .models import Patient, PatientDocument, PatientNote, PatientVitals

class SearchableCountryInput(forms.TextInput):
    """Custom widget for searchable country input"""
    
    def __init__(self, attrs=None):
        default_attrs = {
            'class': 'form-control country-search-input',
            'placeholder': 'Search and select country...',
            'autocomplete': 'off',
            'readonly': True,
            'data-toggle': 'country-dropdown'
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)

class PatientForm(forms.ModelForm):
    """Main patient registration/update form"""
    
    # Override date field to accept string input for DD/MM/YYYY format
    date_of_birth = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            'type': 'text',
            'class': 'form-control modern-date-input date-input-field', 
            'placeholder': 'DD/MM/YYYY',
            'data-bs-toggle': 'tooltip',
            'title': 'Enter date in DD/MM/YYYY format or use calendar button'
        }),
        help_text='Enter date in DD/MM/YYYY format'
    )
    
    class Meta:
        model = Patient
        fields = [
            'patient_id', 'first_name', 'middle_name', 'last_name', 'date_of_birth',
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
            'patient_id': forms.TextInput(attrs={
                'class': 'form-control',
                'readonly': 'readonly',
                'placeholder': 'Auto-generated (HOSPITAL-PAT-XXXXXX)',
                'style': 'background-color: #f8f9fa; color: #6c757d;'
            }),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'blood_group': forms.Select(attrs={'class': 'form-select'}),
            'marital_status': forms.Select(attrs={'class': 'form-select'}),
            'country': SearchableCountryInput(attrs={
                'class': 'form-control country-search-input',
                'placeholder': 'Search and select country...',
                'required': True,
            }),
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
            if field_name not in ['gender', 'blood_group', 'marital_status', 'is_vip', 'profile_picture', 'country']:
                field.widget.attrs['class'] = 'form-control'
            
            # Make certain fields required
            if field_name in ['first_name', 'last_name', 'date_of_birth', 'gender', 'phone', 
                            'address_line1', 'city', 'state', 'postal_code', 'country',
                            'emergency_contact_name', 'emergency_contact_phone']:
                field.required = True
    
    def clean_date_of_birth(self):
        date_of_birth = self.cleaned_data.get('date_of_birth')
        if date_of_birth:
            # If it's already a date object, return it
            if hasattr(date_of_birth, 'year'):
                return date_of_birth
                
            # If it's a string, try to parse DD/MM/YYYY format
            if isinstance(date_of_birth, str):
                from datetime import datetime
                date_formats = ['%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d', '%m/%d/%Y']  # Try multiple formats
                
                for date_format in date_formats:
                    try:
                        parsed_date = datetime.strptime(date_of_birth.strip(), date_format).date()
                        return parsed_date
                    except ValueError:
                        continue
                
                # If none of the formats worked
                raise ValidationError("Please enter a valid date in DD/MM/YYYY format.")
        
        return date_of_birth

    def clean_patient_id(self):
        patient_id = self.cleaned_data.get('patient_id')
        if patient_id:
            # Check if patient ID already exists (for updates, exclude current instance)
            existing = Patient.objects.filter(patient_id=patient_id)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise ValidationError("A patient with this ID already exists.")
        return patient_id
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # Check if email already exists (for updates, exclude current instance)
            existing = Patient.objects.filter(email=email)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise ValidationError("A patient with this email already exists.")
        return email


class QuickPatientForm(forms.ModelForm):
    """Quick patient registration form with minimal fields"""
    
    # Override date field to accept string input for DD/MM/YYYY format
    date_of_birth = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            'type': 'text',
            'class': 'form-control modern-date-input date-input-field', 
            'placeholder': 'DD/MM/YYYY',
            'data-bs-toggle': 'tooltip',
            'title': 'Enter date in DD/MM/YYYY format or use calendar button'
        }),
        help_text='Enter date in DD/MM/YYYY format'
    )
    
    class Meta:
        model = Patient
        fields = [
            'first_name', 'last_name', 'date_of_birth', 'gender', 
            'phone', 'email', 'address_line1', 'city', 'state'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email (optional)'}),
            'address_line1': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Address'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'State'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make required fields
        for field_name in ['first_name', 'last_name', 'date_of_birth', 'gender', 'phone', 'address_line1', 'city', 'state']:
            self.fields[field_name].required = True
    
    def clean_date_of_birth(self):
        date_of_birth = self.cleaned_data.get('date_of_birth')
        if date_of_birth:
            # If it's already a date object, return it
            if hasattr(date_of_birth, 'year'):
                return date_of_birth
                
            # If it's a string, try to parse DD/MM/YYYY format
            if isinstance(date_of_birth, str):
                from datetime import datetime
                date_formats = ['%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d', '%m/%d/%Y']  # Try multiple formats
                
                for date_format in date_formats:
                    try:
                        parsed_date = datetime.strptime(date_of_birth.strip(), date_format).date()
                        return parsed_date
                    except ValueError:
                        continue
                
                # If none of the formats worked
                raise ValidationError("Please enter a valid date in DD/MM/YYYY format.")
        
        return date_of_birth


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
