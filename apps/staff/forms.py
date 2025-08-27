# apps/staff/forms.py
from django import forms
from django.core.exceptions import ValidationError
from apps.accounts.models import CustomUser as User
from .models import Department, StaffProfile


class StaffProfileForm(forms.ModelForm):
    """Main staff profile creation/update form"""
    
    create_user_account = forms.BooleanField(
        required=False,
        initial=True,
        help_text="Create a user account for this staff member to allow system login",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = StaffProfile
        fields = [
            'first_name', 'last_name', 'middle_name', 'position_title',
            'department', 'date_of_birth', 'gender', 'phone_number', 'email',
            'address', 'emergency_contact_name', 'emergency_contact_phone',
            'emergency_contact_relation', 'qualifications', 'certifications',
            'years_of_experience', 'specialization', 'license_number',
            'employment_type', 'joining_date', 'probation_end_date',
            'contract_end_date', 'shift', 'basic_salary', 'hourly_rate',
            'profile_picture', 'bio', 'is_active'
        ]
        
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter first name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter last name'}),
            'middle_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter middle name (optional)'}),
            'position_title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Senior Nurse, Lab Technician'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+1234567890'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'staff@example.com'}),
            'address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Enter full address'}),
            'emergency_contact_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Emergency contact name'}),
            'emergency_contact_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+1234567890'}),
            'emergency_contact_relation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Spouse, Parent'}),
            'qualifications': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Educational qualifications'}),
            'certifications': forms.Textarea(attrs={'rows': 2, 'class': 'form-control', 'placeholder': 'Professional certifications (optional)'}),
            'years_of_experience': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'specialization': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Area of specialization (optional)'}),
            'license_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Professional license number (if applicable)'}),
            'employment_type': forms.Select(attrs={'class': 'form-select'}),
            'joining_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'probation_end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'contract_end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'shift': forms.Select(attrs={'class': 'form-select'}),
            'basic_salary': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'hourly_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'bio': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Brief biography (optional)'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        
        labels = {
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'middle_name': 'Middle Name',
            'position_title': 'Position/Job Title',
            'department': 'Department',
            'date_of_birth': 'Date of Birth',
            'gender': 'Gender',
            'phone_number': 'Phone Number',
            'email': 'Email Address',
            'address': 'Address',
            'emergency_contact_name': 'Emergency Contact Name',
            'emergency_contact_phone': 'Emergency Contact Phone',
            'emergency_contact_relation': 'Emergency Contact Relation',
            'qualifications': 'Educational Qualifications',
            'certifications': 'Professional Certifications',
            'years_of_experience': 'Years of Experience',
            'specialization': 'Specialization',
            'license_number': 'License Number',
            'employment_type': 'Employment Type',
            'joining_date': 'Joining Date',
            'probation_end_date': 'Probation End Date',
            'contract_end_date': 'Contract End Date',
            'shift': 'Work Shift',
            'basic_salary': 'Basic Salary',
            'hourly_rate': 'Hourly Rate',
            'profile_picture': 'Profile Picture',
            'bio': 'Biography',
            'is_active': 'Active Status',
        }
        
        help_texts = {
            'staff_id': 'Auto-generated unique staff ID',
            'position_title': 'Specific job title or position',
            'phone_number': 'Format: +1234567890',
            'email': 'Must be unique in the system',
            'qualifications': 'Educational background and degrees',
            'certifications': 'Professional certifications and licenses',
            'employment_type': 'Type of employment contract',
            'probation_end_date': 'Only for employees on probation',
            'contract_end_date': 'Only for contract employees',
            'basic_salary': 'Monthly basic salary for full-time employees',
            'hourly_rate': 'Hourly rate for part-time/hourly employees',
        }
    
    def __init__(self, hospital=None, *args, **kwargs):
        tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['department'].queryset = Department.objects.filter(tenant=tenant)
        else:
            self.fields['department'].queryset = Department.objects.none()

        # Filter departments by hospital
        if hospital:
            self.fields['department'].queryset = Department.objects.filter(hospital=hospital, is_active=True)
        
        # Set required fields
        required_fields = [
            'first_name', 'last_name', 'position_title', 'date_of_birth', 
            'gender', 'phone_number', 'email', 'address', 'emergency_contact_name',
            'emergency_contact_phone', 'emergency_contact_relation', 'qualifications',
            'employment_type', 'joining_date'
        ]
        
        for field_name in required_fields:
            if field_name in self.fields:
                self.fields[field_name].required = True
        
        # Hide create_user_account field for existing instances
        if self.instance and self.instance.pk:
            del self.fields['create_user_account']
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # Check if email already exists for another staff member
            existing = StaffProfile.objects.filter(email=email)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise ValidationError("A staff member with this email already exists.")
            
            # Check if email exists in User model
            existing_user = User.objects.filter(email=email)
            if self.instance.pk and self.instance.user:
                existing_user = existing_user.exclude(pk=self.instance.user.pk)
            if existing_user.exists():
                raise ValidationError("A user with this email already exists.")
        return email
    
    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if phone:
            # Remove any non-digit characters for validation
            digits_only = ''.join(filter(str.isdigit, phone))
            if len(digits_only) < 10:
                raise ValidationError("Phone number must contain at least 10 digits.")
        return phone
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Validate employment dates
        joining_date = cleaned_data.get('joining_date')
        probation_end_date = cleaned_data.get('probation_end_date')
        contract_end_date = cleaned_data.get('contract_end_date')
        employment_type = cleaned_data.get('employment_type')
        
        if probation_end_date and joining_date:
            if probation_end_date <= joining_date:
                raise ValidationError("Probation end date must be after joining date.")
        
        if contract_end_date and joining_date:
            if contract_end_date <= joining_date:
                raise ValidationError("Contract end date must be after joining date.")
        
        # Validate salary information
        basic_salary = cleaned_data.get('basic_salary')
        hourly_rate = cleaned_data.get('hourly_rate')
        
        if employment_type in ['FULL_TIME', 'PART_TIME'] and not basic_salary and not hourly_rate:
            raise ValidationError("Either basic salary or hourly rate must be specified.")
        
        return cleaned_data


class StaffSearchForm(forms.Form):
    """Staff search and filter form"""
    
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by name, position, email, phone...'
        })
    )
    
    role = forms.ChoiceField(
        choices=[('', 'All Roles')] + [
            ('NO_USER', 'No User Account'),
            ('NURSE', 'Nurses'),
            ('PHARMACIST', 'Pharmacists'),
            ('LAB_TECHNICIAN', 'Lab Technicians'),
            ('RADIOLOGIST', 'Radiologists'),
            ('ACCOUNTANT', 'Accountants'),
            ('HR_MANAGER', 'HR Managers'),
            ('RECEPTIONIST', 'Receptionists'),
            ('STAFF', 'General Staff'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    department = forms.ModelChoiceField(
        queryset=Department.objects.none(),
        required=False,
        empty_label="All Departments",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    employment_type = forms.ChoiceField(
        choices=[('', 'All Employment Types')] + StaffProfile.EMPLOYMENT_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def __init__(self, hospital=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter departments by hospital
        if hospital:
            self.fields['department'].queryset = Department.objects.filter(
                hospital=hospital, is_active=True
            ).order_by('name')


class StaffUserLinkForm(forms.Form):
    """Form for linking existing user to existing staff"""
    
    user = forms.ModelChoiceField(
        queryset=User.objects.none(),  # Will be set in __init__
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Select User to Link',
        help_text='Choose an existing user account to link with this staff member'
    )
    
    def __init__(self, hospital=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if hospital:
            # Get users with staff roles who are not already linked to a staff member or doctor
            self.fields['user'].queryset = User.objects.filter(
                role__in=['NURSE', 'PHARMACIST', 'LAB_TECHNICIAN', 'RADIOLOGIST', 'ACCOUNTANT', 'HR_MANAGER', 'RECEPTIONIST', 'STAFF'],
                hospital=hospital,
                staff_profile__isnull=True,  # Not already linked to a staff
                doctor__isnull=True  # Not linked to a doctor
            ).order_by('first_name', 'last_name')
        
        # Custom display for users
        self.fields['user'].label_from_instance = self._user_label
    
    def _user_label(self, user):
        """Custom label for user dropdown"""
        return f"{user.get_full_name()} ({user.email}) - {user.get_role_display()}"
