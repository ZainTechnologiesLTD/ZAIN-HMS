# doctors/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from apps.accounts.models import CustomUser as User
from .models import Doctor


class DoctorForm(forms.ModelForm):
    """Main doctor creation/update form"""
    
    class Meta:
        model = Doctor
        fields = [
            'first_name', 'last_name', 'specialization', 'license_number',
            'phone_number', 'email', 'date_of_birth', 'address',
            'joining_date', 'image', 'is_active'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter first name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter last name'}),
            'specialization': forms.Select(attrs={'class': 'form-select'}),
            'license_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter license number'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+1234567890'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'doctor@example.com'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Enter address'}),
            'joining_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'specialization': 'Specialization',
            'license_number': 'Medical License Number',
            'phone_number': 'Phone Number',
            'email': 'Email Address',
            'date_of_birth': 'Date of Birth',
            'address': 'Address',
            'joining_date': 'Joining Date',
            'image': 'Profile Picture',
            'is_active': 'Active Status',
        }
        help_texts = {
            'license_number': 'Enter the medical license number',
            'phone_number': 'Format: +1234567890',
            'specialization': 'Select the doctor\'s area of specialization',
            'joining_date': 'Date when the doctor joined the hospital',
        }
    
    def __init__(self, hospital=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hospital = hospital
        
        # Set required fields
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['email'].required = True
        self.fields['license_number'].required = True
        self.fields['specialization'].required = True
        self.fields['joining_date'].required = True
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # Check if email already exists for another doctor
            existing = Doctor.objects.filter(email=email)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise ValidationError("A doctor with this email already exists.")
        return email
    
    def clean_license_number(self):
        license_number = self.cleaned_data.get('license_number')
        if license_number:
            # Check if license number already exists
            existing = Doctor.objects.filter(license_number=license_number)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise ValidationError("A doctor with this license number already exists.")
        return license_number


class DoctorSearchForm(forms.Form):
    """Doctor search and filter form"""
    
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by name, specialization, license...'
        })
    )
    
    specialization = forms.ChoiceField(
        choices=[('', 'All Specializations')] + Doctor.SPECIALIZATION_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class DoctorUserLinkForm(forms.Form):
    """Form for linking existing user to existing doctor"""
    
    user = forms.ModelChoiceField(
        queryset=User.objects.none(),  # Will be set in __init__
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Select User to Link',
        help_text='Choose an existing user account to link with this doctor'
    )
    
    def __init__(self, hospital=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if hospital:
            # Get users with DOCTOR role who are not already linked to a doctor
            self.fields['user'].queryset = User.objects.filter(
                role='DOCTOR',
                hospital=hospital,
                doctor__isnull=True  # Not already linked to a doctor
            ).order_by('first_name', 'last_name')
        
        # Custom display for users
        self.fields['user'].label_from_instance = self._user_label
    
    def _user_label(self, user):
        """Custom label for user dropdown"""
        return f"{user.get_full_name()} ({user.email}) - {user.username}"


class DoctorAdminForm(forms.ModelForm):
    """Form for admin panel doctor management"""
    first_name = forms.CharField(max_length=100)
    last_name = forms.CharField(max_length=100)
    email = forms.EmailField()
    phone_number = forms.CharField(max_length=20)
    address = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = Doctor
        fields = ['first_name', 'last_name', 'email', 'phone_number', 
                 'address', 'specialization', 'license_number', 
                 'date_of_birth', 'joining_date', 'is_active', 'image']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['first_name'].initial = self.instance.user.first_name if self.instance.user else ''
            self.fields['last_name'].initial = self.instance.user.last_name if self.instance.user else ''
            self.fields['email'].initial = self.instance.user.email if self.instance.user else ''
            self.fields['phone_number'].initial = getattr(self.instance.user, 'phone', '') if self.instance.user else ''
            self.fields['address'].initial = getattr(self.instance.user, 'address', '') if self.instance.user else ''