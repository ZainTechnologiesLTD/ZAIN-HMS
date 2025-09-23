# doctors/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from apps.accounts.models import CustomUser as User
from .models import Doctor


class DoctorForm(forms.ModelForm):
    """Main doctor creation/update form"""
    
    # Override date fields to accept string input for DD/MM/YYYY format
    date_of_birth = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            'type': 'text', 
            'class': 'form-control modern-date-input date-input-field', 
            'placeholder': 'DD/MM/YYYY or use date picker',
            'data-bs-toggle': 'tooltip',
            'data-bs-placement': 'top',
            'title': 'Enter date of birth manually or use the calendar picker',
            'autocomplete': 'bday',
            'data-date-format': 'dd/mm/yyyy'
        }),
        help_text='Enter date in DD/MM/YYYY format'
    )
    
    joining_date = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            'type': 'text', 
            'class': 'form-control modern-date-input date-input-field', 
            'placeholder': 'DD/MM/YYYY or use date picker',
            'data-bs-toggle': 'tooltip',
            'data-bs-placement': 'top',
            'title': 'Enter joining date manually or use the calendar picker',
            'data-date-format': 'dd/mm/yyyy'
        }),
        help_text='Enter date in DD/MM/YYYY format'
    )
    
    # Add user account creation option
    create_user_account = forms.BooleanField(
        required=False,
        initial=True,
        help_text="Create a user account for this doctor to allow system login",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    # Add username field for user account
    username = forms.CharField(
        required=False,
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter username for login (e.g., john.smith, dr.john)'
        }),
        help_text="Username for system login (required if creating user account)"
    )
    
    # Add password fields for user account creation
    password = forms.CharField(
        required=False,
        min_length=8,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter password (minimum 8 characters)'
        }),
        help_text="Password for the user account (required if creating user account)"
    )
    
    confirm_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm password'
        }),
        help_text="Re-enter the password to confirm"
    )
    
    class Meta:
        model = Doctor
        fields = [
            'doctor_id', 'first_name', 'last_name', 'specialization', 'license_number',
            'phone_number', 'email', 'date_of_birth', 'address',
            'joining_date', 'image', 'is_active'
        ]
        widgets = {
            'doctor_id': forms.TextInput(attrs={
                'class': 'form-control',
                'readonly': 'readonly',
                'placeholder': 'Auto-generated (DR-YYYY-XXXXXXXX)',
                'style': 'background-color: #f8f9fa; color: #6c757d;'
            }),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter first name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter last name'}),
            'specialization': forms.Select(attrs={'class': 'form-select'}),
            'license_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter license number'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+1234567890'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'doctor@example.com'}),
            'address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Enter address'}),
            'image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'doctor_id': 'Doctor ID',
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
            'doctor_id': 'Unique doctor identification number (auto-generated)',
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
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        create_account = self.cleaned_data.get('create_user_account')
        
        if create_account:
            if not username:
                raise ValidationError("Username is required when creating a user account.")
            
            # Check if username already exists in this hospital
            if hasattr(self, 'hospital') and self.hospital:
                from apps.accounts.models import CustomUser
                existing_user = CustomUser.objects.filter(
                    username=username,
                    hospital__subdomain=self.hospital
                ).first()
                
                if existing_user:
                    raise ValidationError(f"Username '{username}' is already taken in this hospital.")
        
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # Check if email already exists for another doctor in this hospital
            existing = Doctor.objects.filter(email=email)
            # ZAIN HMS unified system - check email uniqueness globally
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise ValidationError("A doctor with this email already exists in this hospital.")
        return email
    
    def clean_confirm_password(self):
        password = self.cleaned_data.get('password')
        confirm_password = self.cleaned_data.get('confirm_password')
        create_account = self.cleaned_data.get('create_user_account')
        username = self.cleaned_data.get('username')
        
        if create_account:
            if not username:
                raise ValidationError("Username is required when creating a user account.")
            if not password:
                raise ValidationError("Password is required when creating a user account.")
            if password != confirm_password:
                raise ValidationError("Passwords do not match.")
        
        return confirm_password
    
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
    
    def clean_joining_date(self):
        joining_date = self.cleaned_data.get('joining_date')
        if joining_date:
            # If it's already a date object, return it
            if hasattr(joining_date, 'year'):
                return joining_date
                
            # If it's a string, try to parse DD/MM/YYYY format
            if isinstance(joining_date, str):
                from datetime import datetime
                date_formats = ['%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d', '%m/%d/%Y']  # Try multiple formats
                
                for date_format in date_formats:
                    try:
                        parsed_date = datetime.strptime(joining_date.strip(), date_format).date()
                        return parsed_date
                    except ValueError:
                        continue
                
                # If none of the formats worked
                raise ValidationError("Please enter a valid date in DD/MM/YYYY format.")
        
        return joining_date
    
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
        
        if True:  # Unified ZAIN HMS system
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