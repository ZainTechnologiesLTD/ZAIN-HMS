# opd/forms.py
from django import forms
from .models import OPD

class OPDForm(forms.ModelForm):
    class Meta:
        model = OPD
        fields = [
            'patient_name', 'patient_age', 'patient_gender',
            'patient_phone', 'patient_email', 'symptoms',
            'diagnosis', 'prescription', 'notes',
            'priority', 'status', 'department',
            'fee', 'is_paid', 'follow_up_date',
            'follow_up_notes'
        ]
        widgets = {
            'symptoms': forms.Textarea(attrs={'rows': 3}),
            'diagnosis': forms.Textarea(attrs={'rows': 3}),
            'prescription': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
            'follow_up_notes': forms.Textarea(attrs={'rows': 2}),
            'follow_up_date': forms.DateInput(attrs={
                'type': 'text',
                'class': 'form-control modern-date-input date-input-field', 
                'placeholder': 'DD/MM/YYYY',
                'data-bs-toggle': 'tooltip',
                'title': 'Enter date in DD/MM/YYYY format or use calendar button'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to form fields
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'