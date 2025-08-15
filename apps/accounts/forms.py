# apps/accounts/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate
from .models import User, Hospital

class CustomAuthenticationForm(AuthenticationForm):
    """Enhanced login form"""
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username or Email',
            'autofocus': True
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password'
        })
    )
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        
        if username and password:
            # Allow login with email or username
            if '@' in username:
                try:
                    user = User.objects.get(email=username)
                    username = user.username
                except User.DoesNotExist:
                    raise forms.ValidationError("Invalid credentials")
            
            self.user_cache = authenticate(
                self.request,
                username=username,
                password=password
            )
            
            if self.user_cache is None:
                raise forms.ValidationError("Invalid username or password")
            else:
                if not self.user_cache.is_active:
                    raise forms.ValidationError("This account is inactive")
                if not self.user_cache.is_approved and self.user_cache.role != 'PATIENT':
                    raise forms.ValidationError("Your account is pending approval")
                    
        return self.cleaned_data


class UserRegistrationForm(UserCreationForm):
    """User registration form"""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email Address'
        })
    )
    first_name = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First Name'
        })
    )
    last_name = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last Name'
        })
    )
    role = forms.ChoiceField(
        choices=[c for c in User.ROLE_CHOICES if c[0] not in ['SUPERADMIN', 'ADMIN']],
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'role', 'password1', 'password2']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if field not in ['role']:
                self.fields[field].widget.attrs['class'] = 'form-control'


class UserProfileForm(forms.ModelForm):
    """User profile update form"""
    class Meta:
        model = User
        fields = [
            'first_name', 'middle_name', 'last_name', 'email',
            'phone', 'alternate_phone', 'date_of_birth', 'gender',
            'blood_group', 'address', 'city', 'state', 'country',
            'postal_code', 'profile_picture', 'bio',
            'emergency_contact_name', 'emergency_contact_phone',
            'emergency_contact_relation'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if field not in ['profile_picture']:
                self.fields[field].widget.attrs['class'] = 'form-control'


class StaffRegistrationForm(UserRegistrationForm):
    """Staff registration form with additional fields"""
    department = forms.ModelChoiceField(
        queryset=None,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    specialization = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    license_number = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    class Meta(UserRegistrationForm.Meta):
        fields = UserRegistrationForm.Meta.fields + [
            'department', 'specialization', 'license_number'
        ]
        
    def __init__(self, hospital=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if hospital:
            self.fields['department'].queryset = Department.objects.filter(
                hospital=hospital, is_active=True
            )