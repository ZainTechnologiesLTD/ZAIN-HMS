# appointments/forms.py

from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import Appointment, Patient, Doctor

class AppointmentForm(forms.ModelForm):
    # Search fields remain the same
    search_name = forms.CharField(required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search by patient name'}))
    search_phone = forms.CharField(required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search by phone number'}))
    search_patient_id = forms.CharField(required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search by patient ID'}))

    # Update doctor field to use doctor_id
    doctor = forms.ModelChoiceField(
        queryset=Doctor.objects.all(),
        widget=forms.HiddenInput(),
        required=True,
        to_field_name='doctor_id'  # This is the key change
    )

    # Keep patient field the same
    patient = forms.ModelChoiceField(
        queryset=Patient.objects.all(),
        widget=forms.HiddenInput(),
        required=True
    )

    # Time field for the selected slot
    time = forms.CharField(
        widget=forms.HiddenInput(),
        required=True
    )

    class Meta:
        model = Appointment
        fields = ['patient', 'doctor', 'appointment_type', 'date_time', 'reason', 'fee']
        exclude = ['created_by', 'status']
        widgets = {
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'date_time': forms.DateTimeInput(attrs={'type': 'datetime-local'})
        }
        labels = {
            'reason': 'Reason for Visit',
            'appointment_type': 'Appointment Type'
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['date_time'].required = False  # We'll set this in clean()
        
        # Make fields required
        required_fields = ['patient', 'doctor', 'appointment_type', 'reason']
        for field in required_fields:
            self.fields[field].required = True

    def clean(self):
        cleaned_data = super().clean()
        
        doctor = cleaned_data.get('doctor')
        time_slot = cleaned_data.get('time')
        
        if doctor and time_slot:
            try:
                # Convert time slot to datetime
                date_time = timezone.make_aware(
                    timezone.datetime.strptime(time_slot, '%Y-%m-%d %H:%M')
                )
                
                # Validate time is not in past
                if date_time < timezone.now():
                    raise ValidationError({
                        'time': "Cannot book appointments in the past."
                    })
                
                # Check for existing appointments
                existing_appointment = Appointment.objects.filter(
                    doctor=doctor,
                    date_time=date_time,
                    status__in=['SCHEDULED', 'CONFIRMED']
                ).exists()
                
                if existing_appointment:
                    raise ValidationError({
                        'time': "This time slot is already booked."
                    })
                
                # Set the date_time field
                cleaned_data['date_time'] = date_time
                
            except ValueError as e:
                raise ValidationError({
                    'time': f"Invalid time slot format: {str(e)}"
                })
        
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Set the date_time and created_by fields
        instance.date_time = self.cleaned_data['date_time']
        instance.created_by = self.user
        
        if commit:
            instance.save()
        
        return instance