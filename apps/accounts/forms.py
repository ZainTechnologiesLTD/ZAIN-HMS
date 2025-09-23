from django import forms
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group
from .models import CustomUser

class LoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your username',
            'id': 'id_username'
        }),
        label='Username'
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password',
            'id': 'id_password'
        })
    )
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

class UserCreateForm(UserCreationForm):
    """Form for creating new users"""
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter first name'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter last name'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter email address'
        })
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter phone number'
        })
    )
    role = forms.ChoiceField(
        choices=CustomUser.ROLE_CHOICES,
        initial='STAFF',
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    is_active = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        help_text="Designates whether this user should be treated as active. Unselect this instead of deleting accounts."
    )

    def __init__(self, *args, **kwargs):
        # Extract current user from kwargs if passed
        self.current_user = kwargs.pop('current_user', None)
        super().__init__(*args, **kwargs)
        
        # Filter role choices based on current user's permissions
        if self.current_user:
            available_roles = self._get_available_roles()
            self.fields['role'].choices = available_roles
    
    def _get_available_roles(self):
        """Get available role choices based on current user's role"""
        if not self.current_user:
            # For frontend forms without authentication, exclude SUPERADMIN role only
            return [choice for choice in CustomUser.ROLE_CHOICES 
                   if choice[0] != 'SUPERADMIN']
        
        # SUPERADMIN role should only be created through Django admin panel
        # Frontend forms should never show SUPERADMIN as an option
        available_choices = [choice for choice in CustomUser.ROLE_CHOICES 
                           if choice[0] != 'SUPERADMIN']
        
        # Super Admins can create any role except SUPERADMIN (through frontend)
        if self.current_user.role == 'SUPERADMIN':
            return available_choices
        
        # Hospital Admins can create all roles except SUPERADMIN
        if self.current_user.role == 'ADMIN':
            return available_choices
        
        # Other roles have limited creation abilities
        if self.current_user.role in ['DOCTOR', 'NURSE']:
            # Medical staff can only create basic staff roles
            return [choice for choice in available_choices 
                   if choice[0] not in ['ADMIN', 'SUPERADMIN']]
        
        # Default: only allow staff role creation for other users
        return [('STAFF', 'General Staff')]

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'phone', 'role', 'is_active', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter username'
            }),
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            # Check username uniqueness in ZAIN HMS database
            existing_user = CustomUser.objects.filter(username=username)
            if self.instance and self.instance.pk:
                existing_user = existing_user.exclude(pk=self.instance.pk)
            if existing_user.exists():
                raise forms.ValidationError(f"Username '{username}' already exists in the system.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError('A user with this email already exists.')
        return email
    
    def clean_role(self):
        """
        SECURITY: Server-side validation to prevent role escalation attacks
        """
        role = self.cleaned_data.get('role')
        
        # SECURITY: Never allow SUPERADMIN role creation through frontend
        if role == 'SUPERADMIN':
            raise forms.ValidationError('SUPERADMIN role can only be created through Django admin by system administrators.')
        
        # SECURITY: Validate current user can assign this role
        if self.current_user:
            allowed_roles = [choice[0] for choice in self._get_available_roles()]
            if role not in allowed_roles:
                raise forms.ValidationError(f'You do not have permission to assign the {role} role.')
        
        return role

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone = self.cleaned_data['phone']
        user.role = self.cleaned_data['role']
        user.is_active = self.cleaned_data.get('is_active', True)
        
        if commit:
            user.save()
        return user


class AdminUserCreationForm(UserCreationForm):
    """Admin add form with additional fields and group assignment."""
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    email = forms.EmailField(required=False)
    phone = forms.CharField(max_length=20, required=False)
    date_of_birth = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    gender = forms.ChoiceField(
        choices=[('', '----')] + CustomUser._meta.get_field('gender').choices,
        required=False
    )
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)
    emergency_contact = forms.CharField(max_length=100, required=False)
    role = forms.ChoiceField(choices=CustomUser.ROLE_CHOICES, required=True)
    employee_id = forms.CharField(max_length=20, required=False)
    is_staff = forms.BooleanField(required=False)
    is_superuser = forms.BooleanField(required=False)
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(), required=False,
        widget=forms.CheckboxSelectMultiple
    )

    class Meta:
        model = CustomUser
        fields = (
            'username', 'password1', 'password2',
            'first_name', 'last_name', 'email', 'phone',
            'date_of_birth', 'gender', 'address', 'emergency_contact',
            'role', 'employee_id',
            'is_staff', 'is_superuser', 'groups'
        )

    def clean_username(self):
        """Validate username uniqueness in ZAIN HMS database"""
        username = self.cleaned_data.get('username')
        if not username:
            return username

        # Check if username already exists in ZAIN HMS
        if CustomUser.objects.filter(username=username).exists():
            raise forms.ValidationError(f"Username '{username}' already exists. Please choose a different username.")

        return username

    def save(self, commit=True):
        user = super().save(commit=False)
        # Set additional attributes
        user.first_name = self.cleaned_data.get('first_name', '')
        user.last_name = self.cleaned_data.get('last_name', '')
        user.email = self.cleaned_data.get('email', '')
        user.phone = self.cleaned_data.get('phone', '')
        user.is_staff = self.cleaned_data.get('is_staff', False)
        user.is_superuser = self.cleaned_data.get('is_superuser', False)

        if commit:
            user.save()
            # Assign groups after user has an ID
            groups = self.cleaned_data.get('groups')
            if groups is not None:
                user.groups.set(groups)
        return user


class UserUpdateForm(forms.ModelForm):
    """Form for updating existing users"""
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter first name'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter last name'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter email address'
        })
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter phone number'
        })
    )
    role = forms.ChoiceField(
        choices=CustomUser.ROLE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    employee_id = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter employee ID'
        })
    )

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'phone', 'role', 'employee_id', 'is_active', 'is_staff')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter username'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_staff': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Exclude current instance from uniqueness check
        if CustomUser.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('A user with this email already exists.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
        return user


class RegistrationForm(forms.ModelForm):
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'required': True
        }),
        label='Password'
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'required': True
        }),
        label='Confirm Password'
    )

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'username', 'email', 'phone', 'date_of_birth', 'gender', 'address']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'required': True
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'required': True
            }),
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'required': True
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'required': True
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'gender': forms.Select(attrs={
                'class': 'form-select'
            }),
            'address': forms.TextInput(attrs={
                'class': 'form-control'
            }),
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            # Check username uniqueness in ZAIN HMS database
            existing_user = CustomUser.objects.filter(username=username)
            if self.instance and self.instance.pk:
                existing_user = existing_user.exclude(pk=self.instance.pk)
            if existing_user.exists():
                raise forms.ValidationError(f"Username '{username}' already exists in the system.")
        return username

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # ZAIN HMS is a single hospital system - no hospital selection needed

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Passwords do not match.')

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        # Set role to PATIENT for patient signup
        user.role = 'PATIENT'
        if commit:
            user.save()
        return user

class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address',
            'id': 'id_email'
        })
    )

class CustomSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new password',
            'id': 'id_new_password1'
        })
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm new password',
            'id': 'id_new_password2'
        })
    )
