# apps/staff/forms.py
from django import forms
from django.core.exceptions import ValidationError
from apps.accounts.models import CustomUser as User
from .models import Department, StaffProfile


class StaffProfileForm(forms.ModelForm):
    """Main staff profile creation/update form"""
    
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
    
    # User Account Creation Fields (following doctor/nurse pattern)
    create_user_account = forms.BooleanField(
        required=False,
        initial=True,
        help_text="Create a user account for this staff member to allow system login",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    # Role selection field (determines permissions and Staff ID generation)
    role = forms.ChoiceField(
        choices=[
            ('PHARMACIST', 'Pharmacist'),
            ('LAB_TECHNICIAN', 'Lab Technician'),
            ('RADIOLOGIST', 'Radiologist'),
            ('ACCOUNTANT', 'Accountant'),
            ('HR_MANAGER', 'HR Manager'),
            ('RECEPTIONIST', 'Receptionist'),
            ('STAFF', 'General Staff'),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_role'
        }),
        help_text='Select the staff member\'s role - determines system permissions'
    )
    
    # Username field for user account
    username = forms.CharField(
        required=False,
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter unique username for login',
            'id': 'id_username'
        }),
        help_text='Must be unique across all hospitals - no auto-generation'
    )
    
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter password (minimum 8 characters)',
            'id': 'id_password',
            'minlength': '8'
        }),
        help_text='Password for system login (minimum 8 characters)',
        min_length=8
    )
    
    password_confirm = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm password',
            'id': 'id_password_confirm',
            'minlength': '8'
        }),
        help_text='Re-enter password to confirm',
        min_length=8,
        label='Confirm Password'
    )
    
    class Meta:
        model = StaffProfile
        fields = [
            'staff_id', 'first_name', 'last_name', 'middle_name',
            'department', 'date_of_birth', 'gender', 'phone_number', 'email',
            'address', 'emergency_contact_name', 'emergency_contact_phone',
            'emergency_contact_relation', 'qualifications', 'certifications',
            'years_of_experience', 'specialization', 'license_number',
            'employment_type', 'joining_date', 'probation_end_date', 'contract_end_date',
            'shift', 'basic_salary', 'hourly_rate',
            'profile_picture', 'bio', 'is_active', 'is_available'
        ]
        
        widgets = {
            'staff_id': forms.TextInput(attrs={
                'class': 'form-control',
                'readonly': 'readonly',
                'placeholder': 'Auto-generated (NUR/PHA/LAB-YYYY-XXXXXXXX)',
                'style': 'background-color: #f8f9fa; color: #6c757d;'
            }),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter first name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter last name'}),
            'middle_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter middle name (optional)'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
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
            'probation_end_date': forms.DateInput(attrs={
                'type': 'text',
                'class': 'form-control modern-date-input date-input-field', 
                'placeholder': 'DD/MM/YYYY',
                'data-bs-toggle': 'tooltip',
                'title': 'Enter date in DD/MM/YYYY format or use calendar button'
            }),
            'contract_end_date': forms.DateInput(attrs={
                'type': 'text',
                'class': 'form-control modern-date-input date-input-field', 
                'placeholder': 'DD/MM/YYYY',
                'data-bs-toggle': 'tooltip',
                'title': 'Enter date in DD/MM/YYYY format or use calendar button'
            }),
            'shift': forms.Select(attrs={'class': 'form-select'}),
            'basic_salary': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'hourly_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'bio': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Brief biography (optional)'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        
        labels = {
            'staff_id': 'Staff ID',
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'middle_name': 'Middle Name',
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
        super().__init__(*args, **kwargs)

        # Set department queryset - show all available departments
        try:
            self.fields['department'].queryset = Department.objects.all()
        except Exception:
            self.fields['department'].queryset = Department.objects.none()
        
        # Set required fields (position_title will be auto-populated based on role)
        required_fields = [
            'first_name', 'last_name', 'department', 'date_of_birth', 
            'gender', 'phone_number', 'email', 'address', 'emergency_contact_name',
            'emergency_contact_phone', 'emergency_contact_relation', 'qualifications',
            'employment_type', 'joining_date'
        ]
        
        print(f"=== FORM INIT DEBUG ===")
        print(f"Hospital: {hospital}")
        print(f"Department queryset count: {Department.objects.count()}")
        print(f"Required fields: {required_fields}")
        
        for field_name in required_fields:
            if field_name in self.fields:
                self.fields[field_name].required = True
                print(f"Set {field_name} as required: {self.fields[field_name].required}")
        
        # Hide create_user_account field for existing instances
        if self.instance and self.instance.pk:
            self.fields['create_user_account'].widget = forms.HiddenInput()
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        create_account = self.cleaned_data.get('create_user_account')
        
        print(f"=== USERNAME VALIDATION ===")
        print(f"Username: {username}")
        print(f"Create account: {create_account}")
        
        if create_account:
            if not username:
                print("ERROR: Username required for user account")
                raise ValidationError("Username is required when creating a user account.")
            
            # Check if username already exists (following doctor pattern)
            existing_user = User.objects.filter(username=username)
            if existing_user.exists():
                print(f"ERROR: Username '{username}' already exists")
                raise ValidationError(f"Username '{username}' is already taken.")
        
        print(f"Username validation passed: {username}")
        return username
    
    # def clean_password_confirm(self):
    #     password = self.cleaned_data.get('password')
    #     password_confirm = self.cleaned_data.get('password_confirm')
    #     create_account = self.cleaned_data.get('create_user_account')
    #     
    #     if create_account:
    #         if not password:
    #             raise ValidationError("Password is required when creating a user account.")
    #         if password != password_confirm:
    #             raise ValidationError("Passwords do not match.")
    #     
    #     return password_confirm
    
    def clean_role(self):
        role = self.cleaned_data.get('role')
        create_account = self.cleaned_data.get('create_user_account')
        
        if create_account and not role:
            raise ValidationError("Role is required when creating a user account.")
            
        return role
    
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
    
    def clean_date_of_birth(self):
        date_of_birth = self.cleaned_data.get('date_of_birth')
        if date_of_birth:
            # If it's already a date object, return it
            if hasattr(date_of_birth, 'year'):
                return date_of_birth
                
            # If it's a string, try to parse DD/MM/YYYY format
            if isinstance(date_of_birth, str):
                from datetime import datetime
                date_formats = ['%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d']  # Try multiple formats
                
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
                date_formats = ['%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d']  # Try multiple formats
                
                for date_format in date_formats:
                    try:
                        parsed_date = datetime.strptime(joining_date.strip(), date_format).date()
                        return parsed_date
                    except ValueError:
                        continue
                
                # If none of the formats worked
                raise ValidationError("Please enter a valid date in DD/MM/YYYY format.")
        
        return joining_date
        
    def clean(self):
        print("=== FORM CLEAN METHOD ===")
        cleaned_data = super().clean()
        print(f"Cleaned data keys: {list(cleaned_data.keys())}")
        
        # Auto-populate position_title based on role if not provided
        role = cleaned_data.get('role')
        position_title = cleaned_data.get('position_title')
        
        if role and not position_title:
            role_titles = {
                'PHARMACIST': 'Pharmacist',
                'LAB_TECHNICIAN': 'Laboratory Technician',
                'RADIOLOGIST': 'Radiologist', 
                'ACCOUNTANT': 'Accountant',
                'HR_MANAGER': 'HR Manager',
                'RECEPTIONIST': 'Receptionist',
                'STAFF': 'General Staff Member',
            }
            cleaned_data['position_title'] = role_titles.get(role, 'Staff Member')
            print(f"Auto-populated position_title: {cleaned_data['position_title']} based on role: {role}")
        
        # Validate employment dates
        joining_date = cleaned_data.get('joining_date')
        probation_end_date = cleaned_data.get('probation_end_date')
        contract_end_date = cleaned_data.get('contract_end_date')
        employment_type = cleaned_data.get('employment_type')
        
        print(f"Date validation - joining: {joining_date}, probation: {probation_end_date}")
        
        if probation_end_date and joining_date:
            if probation_end_date <= joining_date:
                print("ERROR: Probation end date validation failed")
                raise ValidationError("Probation end date must be after joining date.")
        
        if contract_end_date and joining_date:
            if contract_end_date <= joining_date:
                print("ERROR: Contract end date validation failed")
                raise ValidationError("Contract end date must be after joining date.")
        
        # Validate salary information
        basic_salary = cleaned_data.get('basic_salary')
        hourly_rate = cleaned_data.get('hourly_rate')
        
        print(f"Salary validation - basic: {basic_salary}, hourly: {hourly_rate}, type: {employment_type}")
        
        if employment_type in ['FULL_TIME', 'PART_TIME'] and not basic_salary and not hourly_rate:
            print("ERROR: Salary validation failed")
            raise ValidationError("Either basic salary or hourly rate must be specified.")
        
        # Password validation for user account creation
        create_account = cleaned_data.get('create_user_account', False)
        if create_account:
            password = cleaned_data.get('password')
            password_confirm = cleaned_data.get('password_confirm')
            
            print(f"Password validation - password: {'***' if password else 'None'}, confirm: {'***' if password_confirm else 'None'}")
            
            if not password:
                raise ValidationError("Password is required when creating a user account.")
            
            # If password_confirm is missing but we have password, auto-set it
            if password and not password_confirm:
                cleaned_data['password_confirm'] = password
                print("Auto-set password_confirm to match password")
            elif password and password_confirm and password != password_confirm:
                raise ValidationError("Passwords do not match.")
        
        print("Form clean method completed successfully")
        return cleaned_data

    def save(self, commit=True):
        """Save the staff profile"""
        staff = super().save(commit=False)
        
        # Auto-populate position_title based on role from cleaned_data
        role = self.cleaned_data.get('role')
        if role and not staff.position_title:
            role_titles = {
                'PHARMACIST': 'Pharmacist',
                'LAB_TECHNICIAN': 'Laboratory Technician',
                'RADIOLOGIST': 'Radiologist', 
                'ACCOUNTANT': 'Accountant',
                'HR_MANAGER': 'HR Manager',
                'RECEPTIONIST': 'Receptionist',
                'STAFF': 'General Staff Member',
            }
            staff.position_title = role_titles.get(role, 'Staff Member')
            print(f"Save method: Set position_title to '{staff.position_title}' based on role '{role}'")
        
        if commit:
            staff.save()
            
        return staff


class StaffUserAccountForm(forms.Form):
    """Separate form for creating user accounts for staff members"""
    
    # Role selection field (determines permissions and Staff ID generation)
    role = forms.ChoiceField(
        choices=[
            ('PHARMACIST', 'Pharmacist'),
            ('LAB_TECHNICIAN', 'Lab Technician'),
            ('RADIOLOGIST', 'Radiologist'),
            ('ACCOUNTANT', 'Accountant'),
            ('HR_MANAGER', 'HR Manager'),
            ('RECEPTIONIST', 'Receptionist'),
            ('STAFF', 'General Staff'),
        ],
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_role'
        }),
        help_text='Select the staff member\'s role - this will determine their system permissions and auto-generate appropriate Staff ID'
    )
    
    # User account fields
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter unique username for login',
            'id': 'id_username'
        }),
        help_text='Must be unique across all hospitals - no auto-generation'
    )
    
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter password (minimum 8 characters)',
            'id': 'id_password',
            'minlength': '8'
        }),
        help_text='Password for system login (minimum 8 characters)',
        min_length=8
    )
    
    password_confirm = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm password',
            'id': 'id_password_confirm',
            'minlength': '8'
        }),
        help_text='Re-enter password to confirm',
        min_length=8,
        label='Confirm Password'
    )
    
    # User account creation toggle (required as per frontend)
    create_user_account = forms.BooleanField(
        required=True,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'id_create_user_account',
            'checked': 'checked'
        }),
        help_text='System login account is required for all staff members'
    )
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            # Check username uniqueness across ALL hospital databases
            from django.db import connections
            from django.conf import settings
            import os
            
            # Check main database first
            existing_user = User.objects.filter(username=username)
            if existing_user.exists():
                raise ValidationError(f"Username '{username}' already exists in the system.")
            
            # Check all hospital databases
            hospitals_dir = os.path.join(settings.BASE_DIR, 'hospitals')
            if os.path.exists(hospitals_dir):
                for hospital_folder in os.listdir(hospitals_dir):
                    db_path = os.path.join(hospitals_dir, hospital_folder, 'db.sqlite3')
                    if os.path.exists(db_path):
                        try:# 
                            hospital_db = f'hospital_{hospital_folder}'
                            if hospital_db in settings.DATABASES:
                                users_in_hospital = User.objects.filter(username=username)
                                if users_in_hospital.exists():
                                    raise ValidationError(f"Username '{username}' already exists in {hospital_folder} hospital.")
                        except Exception:
                            continue
        return username

    def clean(self):
        cleaned_data = super().clean()
        
        # Password confirmation validation
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password_confirm:
            if password != password_confirm:
                raise ValidationError("Passwords do not match.")
        
        return cleaned_data

    def create_user_for_staff(self, staff_profile):
        """Create user account for the given staff profile"""
        if self.cleaned_data.get('create_user_account'):
            role = self.cleaned_data.get('role', 'STAFF')
            username = self.cleaned_data.get('username')
            password = self.cleaned_data.get('password')
            
            # Create the user with manually entered credentials
            user = User.objects.create_user(
                username=username,
                password=password,
                email=staff_profile.email,
                first_name=staff_profile.first_name,
                last_name=staff_profile.last_name,
                role=role,
                is_active=True,
                phone=staff_profile.phone_number,
                gender=staff_profile.gender,
                date_of_birth=staff_profile.date_of_birth,
            )
            
            # Link user to staff profile
            staff_profile.user = user
            staff_profile.save()
            
            return user
        return None


class StaffProfileWithUserForm(forms.Form):
    """Combined form that handles both staff profile and user account creation"""
    
    def __init__(self, *args, **kwargs):
        # Extract specific kwargs for each sub-form
        instance = kwargs.pop('instance', None)
        hospital = kwargs.pop('hospital', None)
        
        # Initialize the parent form
        super().__init__(*args, **kwargs)
        
        # Create kwargs for staff profile form
        staff_kwargs = {}
        if args:
            staff_kwargs['data'] = args[0] if args else None
        if instance:
            staff_kwargs['instance'] = instance
        if True:  # Unified ZAIN HMS system
            staff_kwargs['hospital'] = hospital
            
        # Create kwargs for user form
        user_kwargs = {}
        if args:
            user_kwargs['data'] = args[0] if args else None
        
        # Initialize sub-forms
        self.staff_form = StaffProfileForm(**staff_kwargs)
        self.user_form = StaffUserAccountForm(**user_kwargs)
    
    def is_valid(self):
        return self.staff_form.is_valid() and self.user_form.is_valid()
    
    @property
    def errors(self):
        """Combine errors from both forms"""
        combined_errors = {}
        if hasattr(self.staff_form, 'errors'):
            combined_errors.update(self.staff_form.errors)
        if hasattr(self.user_form, 'errors'):
            combined_errors.update(self.user_form.errors)
        return combined_errors
    
    def save(self, commit=True):
        # Save staff profile first
        staff = self.staff_form.save(commit=commit)
        
        # Create user account
        user = self.user_form.create_user_for_staff(staff)
        
        # Update staff position based on role if user was created
        if user:
            role = self.user_form.cleaned_data.get('role', 'STAFF')
            role_titles = {
                'PHARMACIST': 'Pharmacist',
                'LAB_TECHNICIAN': 'Laboratory Technician',
                'RADIOLOGIST': 'Radiologist',
                'ACCOUNTANT': 'Accountant',
                'HR_MANAGER': 'HR Manager',
                'RECEPTIONIST': 'Receptionist',
                'STAFF': 'General Staff Member',
            }
            staff.position_title = role_titles.get(role, 'Staff Member')
            if commit:
                staff.save()
        
        return staff


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
        
        # Set department queryset - show all available departments
        try:
            self.fields['department'].queryset = Department.objects.all().order_by('name')
        except Exception:
            self.fields['department'].queryset = Department.objects.none()




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
        
        if True:  # Unified ZAIN HMS system
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
