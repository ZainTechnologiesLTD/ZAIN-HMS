from django import forms
from .models import EmergencyCase, EmergencyTreatment

class EmergencyCaseForm(forms.ModelForm):
    class Meta:
        model = EmergencyCase
        fields = [
            'patient_name', 'age', 'contact_number', 'chief_complaint',
            'priority', 'status', 'assigned_doctor', 'vital_signs', 'notes'
        ]
        widgets = {
            'patient_name': forms.TextInput(attrs={'class': 'form-control'}),
            'age': forms.NumberInput(attrs={'class': 'form-control'}),
            'contact_number': forms.TextInput(attrs={'class': 'form-control'}),
            'chief_complaint': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'assigned_doctor': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['vital_signs'].widget = forms.HiddenInput()
        
        # Add Bootstrap classes to all fields
        for field in self.fields:
            if 'class' not in self.fields[field].widget.attrs:
                self.fields[field].widget.attrs['class'] = 'form-control'

class EmergencyTreatmentForm(forms.ModelForm):
    class Meta:
        model = EmergencyTreatment
        fields = ['procedure', 'medications', 'notes']
        widgets = {
            'procedure': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter procedure details'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter additional notes'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['medications'].widget = forms.HiddenInput()
        
        # Add Bootstrap classes to all fields
        for field in self.fields:
            if 'class' not in self.fields[field].widget.attrs:
                self.fields[field].widget.attrs['class'] = 'form-control'