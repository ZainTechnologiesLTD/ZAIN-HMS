# doctors/forms.py
from django import forms
from .models import Doctor

class DoctorAdminForm(forms.ModelForm):
    first_name = forms.CharField(max_length=100)
    last_name = forms.CharField(max_length=100)
    email = forms.EmailField()
    phone_number = forms.CharField(max_length=20)
    address = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = Doctor
        fields = ['first_name', 'last_name', 'email', 'phone_number', 
                 'address', 'specialization', 'license_number', 
                 'date_of_birth', 'joining_date', 'is_active', 'image']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email
            self.fields['phone_number'].initial = self.instance.user.phone
            self.fields['address'].initial = self.instance.user.address