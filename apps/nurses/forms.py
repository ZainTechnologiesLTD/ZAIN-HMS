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
    class Meta:
        model = Nurse
        exclude = ['user', 'created_at', 'updated_at']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'joining_date': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 3}),
            'qualifications': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if not phone_number.isdigit():
            raise forms.ValidationError('Phone number should contain only digits.')
        return phone_number

    def clean(self):
        cleaned_data = super().clean()
        joining_date = cleaned_data.get('joining_date')
        date_of_birth = cleaned_data.get('date_of_birth')
        
        if joining_date and date_of_birth:
            if joining_date < date_of_birth:
                raise forms.ValidationError('Joining date cannot be earlier than date of birth.')
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