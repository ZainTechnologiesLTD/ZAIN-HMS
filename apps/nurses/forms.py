from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Department, Nurse, NurseSchedule, NurseLeave

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField()
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']

class NurseForm(forms.ModelForm):
    # User fields for account creation
    first_name = forms.CharField(
        max_length=30, 
        help_text="Will be used for user account",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter first name'})
    )
    last_name = forms.CharField(
        max_length=30, 
        help_text="Will be used for user account",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter last name'})
    )
    email = forms.EmailField(
        help_text="Contact email address (not used for login)",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email address'})
    )
    
    # Add username field for login
    username = forms.CharField(
        max_length=30,
        required=True,  # Make it mandatory
        label="Username *",
        help_text="Login username (must be unique across all hospitals)",
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Enter unique username (e.g., sarah.jones)',
            'id': 'id_username'
        })
    )
    
    # Employee ID field - read-only and auto-generated
    employee_id = forms.CharField(
        required=False,
        label="Employee ID",
        help_text="Auto-generated when saving",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'readonly': 'readonly',
            'placeholder': 'Will be auto-generated (NUR-YYYY-XXXXXXXX)',
            'style': 'background-color: #f8f9fa; color: #6c757d;'
        })
    )
    
    # Override date fields to accept string input for DD/MM/YYYY format
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
    
    joining_date = forms.CharField(
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
    
    # Add user account creation option
    create_user_account = forms.BooleanField(
        required=False,
        initial=True,
        label="Create User Account",
        help_text="Create a system login account for this nurse (uses username for login)",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    # Add password fields for user account creation
    password = forms.CharField(
        required=False,
        min_length=8,
        label="Login Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter password (minimum 8 characters)'
        }),
        help_text="Password for system login"
    )
    
    confirm_password = forms.CharField(
        required=False,
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm password'
        }),
        help_text="Re-enter the password to confirm"
    )
    
    class Meta:
        model = Nurse
        exclude = ['user', 'employee_id', 'created_at', 'updated_at']
        widgets = {
            'department': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': 'Select Department'
            }),
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter phone number'}),
            'address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Enter address'}),
            'qualifications': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Enter qualifications'}),
            'years_of_experience': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'placeholder': 'Years of experience'}),
            'shift': forms.Select(attrs={'class': 'form-select'}),
            'joining_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'salary': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Enter salary'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        # Extract database parameter if provided
        # database_name removed; unified single DB assumed
        super().__init__(*args, **kwargs)

        # Ensure department field has proper queryset using the default DB
        from apps.staff.models import Department
        try:
            departments = Department.objects.all().order_by('name')
            self.fields['department'].queryset = departments
            self.fields['department'].empty_label = "Select a department"
        except Exception:
            # If there's an issue loading departments, provide a helpful error
            self.fields['department'].choices = [('', 'No departments available')]
        
        # Set field requirements and help text
        self.fields['department'].required = True
        self.fields['shift'].required = True
        self.fields['date_of_birth'].required = True
        self.fields['gender'].required = True
        self.fields['phone_number'].required = True
        self.fields['joining_date'].required = True
        
        # Employee ID is auto-generated, so it's not required for form validation
        self.fields['employee_id'].required = False
        
        # If this is an existing nurse, show the employee_id
        if self.instance and self.instance.pk:
            self.fields['employee_id'].initial = self.instance.employee_id
        else:
            # For new nurses, show a preview of what the ID will look like
            from django.utils import timezone
            import uuid
            preview_id = f"NUR-{timezone.now().year}-{str(uuid.uuid4())[:8].upper()}"
            self.fields['employee_id'].widget.attrs['placeholder'] = f"Will be auto-generated (e.g., {preview_id})"

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if not phone_number.isdigit():
            raise forms.ValidationError('Phone number should contain only digits.')
        return phone_number

    def clean_email(self):
        email = self.cleaned_data.get('email')
        # In username-based system, email doesn't need to be unique
        # Multiple nurses can have the same email across different hospitals
        return email
    
    def clean_employee_id(self):
        employee_id = self.cleaned_data.get('employee_id')
        # Employee ID will be auto-generated, so we don't validate it here
        # Return None or empty string to let the model generate it
        return None if not employee_id else employee_id
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        
        if not username:
            raise forms.ValidationError("Username is required.")
            
        # Check username uniqueness across ALL hospital databases
        from apps.accounts.models import CustomUser
        from django.db import connections
        from django.conf import settings
        import os
        
        # Get all hospital database connections
        hospital_dbs = []
        hospitals_dir = os.path.join(settings.BASE_DIR, 'hospitals')
        if os.path.exists(hospitals_dir):
            for hospital_folder in os.listdir(hospitals_dir):
                db_path = os.path.join(hospitals_dir, hospital_folder, 'db.sqlite3')
                if os.path.exists(db_path):
                    hospital_dbs.append(hospital_folder)
        
        # Check main database
        if CustomUser.objects.filter(username=username).exists():
            raise forms.ValidationError(
                f'Username "{username}" is already taken in the main system. '
                f'Try: {self.generate_username_suggestions(username)}'
            )
        
        # Single database setup - already checked above in main database check
                
        return username
    
    def generate_username_suggestions(self, username):
        """Generate username suggestions"""
        suggestions = []
        base_username = username.lower()
        
        # Get first and last name for better suggestions
        first_name = self.cleaned_data.get('first_name', '').lower()
        last_name = self.cleaned_data.get('last_name', '').lower()
        
        # Generate various suggestions
        if first_name and last_name:
            suggestions.extend([
                f"{first_name}.{last_name}",
                f"{first_name[0]}.{last_name}",
                f"{first_name}.{last_name[0]}",
                f"{first_name}{last_name}",
                f"{last_name}.{first_name}",
            ])
        
        # Add numbered variations
        for i in range(2, 6):
            suggestions.append(f"{base_username}{i}")
            if first_name and last_name:
                suggestions.append(f"{first_name}.{last_name}{i}")
        
        # Remove duplicates and the original username
        suggestions = list(dict.fromkeys(suggestions))  # Remove duplicates
        if username in suggestions:
            suggestions.remove(username)
            
        return ", ".join(suggestions[:5])  # Return top 5 suggestions

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
                raise forms.ValidationError("Please enter a valid date in DD/MM/YYYY format.")
        
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
                raise forms.ValidationError("Please enter a valid date in DD/MM/YYYY format.")
        
        return joining_date

    def clean(self):
        cleaned_data = super().clean()
        joining_date = cleaned_data.get('joining_date')
        date_of_birth = cleaned_data.get('date_of_birth')
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        create_account = cleaned_data.get('create_user_account')
        username = cleaned_data.get('username')
        
        if joining_date and date_of_birth:
            if joining_date < date_of_birth:
                raise forms.ValidationError('Joining date cannot be earlier than date of birth.')
        
        # Username is now mandatory, no auto-generation needed
        if create_account and not username:
            raise forms.ValidationError("Username is required when creating a user account.")
        
        # Validate passwords if creating user account
        if create_account:
            if not password:
                raise forms.ValidationError("Password is required when creating a user account.")
            if password != confirm_password:
                raise forms.ValidationError("Passwords do not match.")
        
        return cleaned_data

class NurseScheduleForm(forms.ModelForm):
    class Meta:
        model = NurseSchedule
        exclude = ['nurse', 'created_at', 'updated_at']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        if start_time and end_time and start_time >= end_time:
            raise forms.ValidationError('End time must be later than start time.')
        return cleaned_data

class NurseLeaveForm(forms.ModelForm):
    class Meta:
        model = NurseLeave
        exclude = ['nurse', 'status', 'approved_by', 'created_at', 'updated_at']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'reason': forms.Textarea(attrs={'rows': 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError('End date must be later than or equal to start date.')
        return cleaned_data

class NurseSearchForm(forms.Form):
    search = forms.CharField(required=False)
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=False,
        empty_label="All Departments"
    )
    shift = forms.ChoiceField(
        choices=[('', 'All Shifts')] + Nurse.SHIFT_CHOICES,
        required=False
    )