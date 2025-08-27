# apps/appointments/forms.py
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Appointment, AppointmentType
from apps.patients.models import Patient
from apps.doctors.models import Doctor

class AppointmentForm(forms.ModelForm):
    """Main appointment creation/update form"""
    
    class Meta:
        model = Appointment
        fields = [
            'patient', 'doctor', 'appointment_date',
            'appointment_time', 'duration_minutes', 'priority',
            'chief_complaint', 'symptoms', 'notes', 'consultation_fee',
            'is_follow_up', 'previous_appointment'
        ]
        widgets = {
            'patient': forms.Select(attrs={'class': 'form-select'}),
            'doctor': forms.Select(attrs={'class': 'form-select'}),
            'appointment_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'appointment_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'duration_minutes': forms.NumberInput(attrs={'class': 'form-control', 'min': '15', 'max': '240', 'value': '30'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'chief_complaint': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Describe the main reason for this appointment...'}),
            'symptoms': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'List any symptoms the patient is experiencing...'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Additional notes or special instructions...'}),
            'consultation_fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'is_follow_up': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'previous_appointment': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'patient': 'Patient',
            'doctor': 'Doctor',
            'appointment_date': 'Appointment Date',
            'appointment_time': 'Appointment Time',
            'duration_minutes': 'Duration (minutes)',
            'priority': 'Priority',
            'chief_complaint': 'Chief Complaint',
            'symptoms': 'Symptoms',
            'notes': 'Additional Notes',
            'consultation_fee': 'Consultation Fee',
            'is_follow_up': 'Follow-up Appointment',
            'previous_appointment': 'Previous Appointment',
        }
        help_texts = {
            'chief_complaint': 'The main reason for this appointment',
            'symptoms': 'Current symptoms the patient is experiencing',
            'notes': 'Any additional notes or special instructions',
            'duration_minutes': 'Expected duration of the appointment (15-240 minutes)',
            'consultation_fee': 'Fee for this consultation in USD',
        }
    
    def __init__(self, *args, **kwargs):
        # Accept both tenant and hospital for backward compatibility
        tenant = kwargs.pop('tenant', None)
        hospital = kwargs.pop('hospital', None)
        
        # Use tenant if provided, otherwise use hospital
        if tenant:
            hospital = tenant
            
        super().__init__(*args, **kwargs)
        
        if hospital:
            # Determine the correct database
            db_alias = f'hospital_{hospital}' if hospital else 'default'
            
            # Filter patients by hospital/tenant
            # NOTE: tenant field is temporarily commented out in Patient model
            self.fields['patient'].queryset = Patient.objects.using(db_alias).filter(
                is_active=True
            ).order_by('first_name', 'last_name')
            
            # Avoid cross-database queries for Doctor filtering
            from apps.accounts.models import CustomUser as User
            
            # Since tenant field is temporarily commented out, get all doctor users for now
            # TODO: Implement proper hospital-user filtering when tenant system is fixed
            hospital_user_ids = list(User.objects.using('default').filter(
                role='DOCTOR'
            ).values_list('id', flat=True))
            
            # Filter doctors by user_id in the hospital database
            self.fields['doctor'].queryset = Doctor.objects.using(db_alias).filter(
                user_id__in=hospital_user_ids,
                is_active=True
            ).order_by('first_name', 'last_name')
            
            # NOTE: appointment_type field is temporarily disabled due to missing database column
        else:
            # If no tenant/hospital, show empty querysets
            self.fields['patient'].queryset = Patient.objects.none()
            self.fields['doctor'].queryset = Doctor.objects.none()
            
            # Handle previous appointments
            if self.instance.pk and hasattr(self.instance, 'patient') and self.instance.patient:
                self.fields['previous_appointment'].queryset = Appointment.objects.filter(
                    patient=self.instance.patient,
                    status='COMPLETED'
                ).exclude(pk=self.instance.pk).order_by('-appointment_date')
            else:
                self.fields['previous_appointment'].queryset = Appointment.objects.none()
        
        # Set minimum date to today
        self.fields['appointment_date'].widget.attrs['min'] = timezone.now().date().isoformat()
        
        # Make required fields more obvious
        self.fields['patient'].required = True
        self.fields['doctor'].required = True
        self.fields['appointment_date'].required = True
        self.fields['appointment_time'].required = True
        self.fields['chief_complaint'].required = True
    
    def clean(self):
        cleaned_data = super().clean()
        appointment_date = cleaned_data.get('appointment_date')
        appointment_time = cleaned_data.get('appointment_time')
        doctor = cleaned_data.get('doctor')
        
        if appointment_date and appointment_time:
            # Check if appointment is in the future
            appointment_datetime = timezone.make_aware(
                timezone.datetime.combine(appointment_date, appointment_time)
            )
            if appointment_datetime <= timezone.now():
                raise ValidationError("Appointment must be scheduled for a future date and time.")
            
            # Check doctor availability
            if doctor:
                conflicting_appointments = Appointment.objects.filter(
                    doctor=doctor,
                    appointment_date=appointment_date,
                    appointment_time=appointment_time,
                    status__in=['SCHEDULED', 'CONFIRMED', 'CHECKED_IN', 'IN_PROGRESS']
                )
                
                if self.instance.pk:
                    conflicting_appointments = conflicting_appointments.exclude(pk=self.instance.pk)
                
                if conflicting_appointments.exists():
                    raise ValidationError("Doctor is not available at the selected time.")
        
        return cleaned_data


class QuickAppointmentForm(forms.ModelForm):
    """Quick appointment scheduling form"""
    
    class Meta:
        model = Appointment
        fields = [
            'patient', 'doctor', 'appointment_date', 'appointment_time',
            'chief_complaint', 'consultation_fee'
        ]
        widgets = {
            'patient': forms.Select(attrs={'class': 'form-select'}),
            'doctor': forms.Select(attrs={'class': 'form-select'}),
            'appointment_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'appointment_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'chief_complaint': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'consultation_fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
    
    def __init__(self, *args, **kwargs):
        # Accept both tenant and hospital for backward compatibility
        tenant = kwargs.pop('tenant', None)
        hospital = kwargs.pop('hospital', None)
        
        # Use tenant if provided, otherwise use hospital
        if tenant:
            hospital = tenant
            
        super().__init__(*args, **kwargs)
        if hospital:
            # Determine the correct database
            db_alias = f'hospital_{hospital}' if hospital else 'default'
            
            # NOTE: tenant field is temporarily commented out in Patient model
            self.fields['patient'].queryset = Patient.objects.using(db_alias).filter(
                is_active=True
            )
            
            # Avoid cross-database queries for Doctor filtering
            from apps.accounts.models import CustomUser as User
            
            # Since tenant field is temporarily commented out, get all doctor users for now
            # TODO: Implement proper hospital-user filtering when tenant system is fixed
            hospital_user_ids = list(User.objects.using('default').filter(
                role='DOCTOR'
            ).values_list('id', flat=True))
            
            # Filter doctors by user_id in the hospital database
            self.fields['doctor'].queryset = Doctor.objects.using(db_alias).filter(
                user_id__in=hospital_user_ids,
                is_active=True
            )
        else:
            # If no tenant/hospital, show empty querysets
            self.fields['patient'].queryset = Patient.objects.none()
            self.fields['doctor'].queryset = Doctor.objects.none()


class AppointmentSearchForm(forms.Form):
    """Appointment search and filter form"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by patient name, doctor, or appointment number...'
        })
    )
    
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + Appointment.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    priority = forms.ChoiceField(
        choices=[('', 'All Priorities')] + Appointment.PRIORITY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    doctor = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="All Doctors",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def __init__(self, *args, **kwargs):
        # Accept both tenant and hospital for backward compatibility
        tenant = kwargs.pop('tenant', None)
        hospital = kwargs.pop('hospital', None)
        
        # Use tenant if provided, otherwise use hospital
        if tenant:
            hospital = tenant
        
        super().__init__(*args, **kwargs)
        if hospital:
            # Avoid cross-database queries for Doctor filtering
            from apps.accounts.models import CustomUser as User
            
            # Since tenant field is temporarily commented out, get all doctor users for now
            # TODO: Implement proper hospital-user filtering when tenant system is fixed
            hospital_user_ids = list(User.objects.using('default').filter(
                role='DOCTOR'
            ).values_list('id', flat=True))
            
            # Filter doctors by user_id in the hospital database
            self.fields['doctor'].queryset = Doctor.objects.filter(
                user_id__in=hospital_user_ids,
                is_active=True
            )


class RescheduleAppointmentForm(forms.Form):
    """Form for rescheduling appointments"""
    
    new_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    new_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'})
    )
    reason = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        help_text="Reason for rescheduling"
    )
    
    def __init__(self, appointment=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.appointment = appointment
        # Set minimum date to today
        self.fields['new_date'].widget.attrs['min'] = timezone.now().date().isoformat()
    
    def clean(self):
        cleaned_data = super().clean()
        new_date = cleaned_data.get('new_date')
        new_time = cleaned_data.get('new_time')
        
        if new_date and new_time and self.appointment:
            # Check if new time is in the future
            new_datetime = timezone.make_aware(
                timezone.datetime.combine(new_date, new_time)
            )
            if new_datetime <= timezone.now():
                raise ValidationError("New appointment time must be in the future.")
            
            # Check doctor availability
            conflicting_appointments = Appointment.objects.filter(
                doctor=self.appointment.doctor,
                appointment_date=new_date,
                appointment_time=new_time,
                status__in=['SCHEDULED', 'CONFIRMED', 'CHECKED_IN', 'IN_PROGRESS']
            ).exclude(pk=self.appointment.pk)
            
            if conflicting_appointments.exists():
                raise ValidationError("Doctor is not available at the new selected time.")
        
        return cleaned_data


class CancelAppointmentForm(forms.Form):
    """Form for cancelling appointments"""
    
    reason = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        help_text="Reason for cancellation"
    )
    
    notify_patient = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Send cancellation notification to patient",
    )