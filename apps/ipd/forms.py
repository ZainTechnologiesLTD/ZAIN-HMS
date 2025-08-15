# ipd/forms.py
from django import forms
from .models import IPDRecord

class IPDRecordForm(forms.ModelForm):
    class Meta:
        model = IPDRecord
        fields = ['patient', 'doctor', 'room', 'bed', 'status']
        widgets = {
            'patient': forms.Select(attrs={'class': 'form-select select2'}),
            'doctor': forms.Select(attrs={'class': 'form-select select2'}),
            'room': forms.Select(attrs={'class': 'form-select'}),
            'bed': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }