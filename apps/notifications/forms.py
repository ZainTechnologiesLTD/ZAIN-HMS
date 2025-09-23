# notifications/forms.py
from django import forms
from .models import Notification, NotificationTemplate
from apps.patients.models import Patient
from django.contrib.auth import get_user_model

User = get_user_model()

class NotificationForm(forms.ModelForm):
    """Form for hospital admins to create notifications"""
    
    recipients = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),  # Will be set in __init__
        widget=forms.CheckboxSelectMultiple,
        required=True,
        help_text="Select users to send notification to"
    )
    
    class Meta:
        model = Notification
        fields = ['recipients', 'level', 'title', 'message', 'action_url']
        widgets = {
            'level': forms.Select(attrs={
                'class': 'form-select',
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter notification title...'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter notification message...'
            }),
            'action_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'Optional: Enter URL for action button'
            })
        }
    
    def __init__(self, *args, hospital_context=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set recipients based on hospital context
        # In unified system, ignore database_name and use default DB
        self.fields['recipients'].queryset = User.objects.filter(
            is_active=True
        ).exclude(is_superuser=True)
        
        # Add Bootstrap classes
        for field_name, field in self.fields.items():
            if field_name != 'recipients':
                if 'class' not in field.widget.attrs:
                    field.widget.attrs['class'] = 'form-control'

class BulkNotificationForm(forms.Form):
    """Form for sending bulk notifications to patient groups"""
    
    RECIPIENT_CHOICES = [
        ('all_patients', 'All Patients'),
        ('recent_patients', 'Patients from Last 30 Days'),
        ('custom_group', 'Custom Patient Group'),
    ]
    
    recipient_type = forms.ChoiceField(
        choices=RECIPIENT_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='all_patients'
    )
    
    custom_patients = forms.ModelMultipleChoiceField(
        queryset=Patient.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text="Select specific patients (only used with Custom Patient Group)"
    )
    
    level = forms.ChoiceField(
        choices=Notification.LEVELS,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    title = forms.CharField(
        max_length=250,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter notification title...'
        })
    )
    
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Enter notification message...'
        })
    )
    
    action_url = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'Optional: Enter URL for action button'
        })
    )
    
    def __init__(self, *args, hospital_context=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set patients based on hospital context
        # In unified system, simply use default DB
        self.fields['custom_patients'].queryset = Patient.objects.all()
