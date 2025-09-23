from django import forms
from .models import EmergencyCase, EmergencyMedication

class EmergencyCaseForm(forms.ModelForm):
    class Meta:
        model = EmergencyCase
        fields = ['case_number', 'patient_name']
        widgets = {
            'case_number': forms.TextInput(attrs={'class': 'form-control'}),
            'patient_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if 'class' not in self.fields[field].widget.attrs:
                self.fields[field].widget.attrs['class'] = 'form-control'

class EmergencyTreatmentForm(forms.ModelForm):
    class Meta:
        model = EmergencyMedication
        fields = ['medication_name', 'dosage', 'route', 'frequency', 'indication', 'notes']
        widgets = {
            'medication_name': forms.TextInput(attrs={'class': 'form-control'}),
            'dosage': forms.TextInput(attrs={'class': 'form-control'}),
            'route': forms.TextInput(attrs={'class': 'form-control'}),
            'frequency': forms.TextInput(attrs={'class': 'form-control'}),
            'indication': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if 'class' not in self.fields[field].widget.attrs:
                self.fields[field].widget.attrs['class'] = 'form-control'