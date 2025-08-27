from django.apps import AppConfig
from django import forms


class DoctorsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.doctors'

    def ready(self):
        # Import models inside the ready() method to avoid AppRegistryNotReady error
        from .models import Doctor

        # Define the form dynamically here if needed
        class DoctorForm(forms.ModelForm):
            class Meta:
                model = Doctor
                fields = [
                    'first_name', 'last_name', 'specialization', 'license_number',
                    'phone_number', 'email', 'date_of_birth', 'address',
                    'image', 'joining_date', 'is_active'
                ]
                widgets = {
                    'joining_date': forms.DateInput(attrs={'type': 'date'}),
                    'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
                }

        # Optionally register the form if needed elsewhere in the app
        self.doctor_form = DoctorForm
