# ipd/forms.py
from django import forms
from .models import IPDRecord, Bed

class IPDRecordForm(forms.ModelForm):
    class Meta:
        model = IPDRecord
        fields = ['patient', 'attending_doctor', 'referring_doctor', 'diagnosis', 'room', 'bed', 'status']
        widgets = {
            'patient': forms.Select(attrs={'class': 'form-select select2'}),
            'attending_doctor': forms.Select(attrs={'class': 'form-select select2'}),
            'referring_doctor': forms.Select(attrs={'class': 'form-select select2'}),
            'diagnosis': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'room': forms.Select(attrs={'class': 'form-select'}),
            'bed': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show available beds
        self.fields['bed'].queryset = Bed.objects.filter(available=True)