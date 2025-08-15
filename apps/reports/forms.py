# apps/reports/forms.py
from django import forms
from django.utils import timezone
from .models import Report, ReportTemplate

class ReportGenerationForm(forms.ModelForm):
    """Form for generating reports"""
    
    class Meta:
        model = Report
        fields = ['name', 'report_type', 'format', 'date_from', 'date_to']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter report name'
            }),
            'report_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'format': forms.Select(attrs={
                'class': 'form-select'
            }),
            'date_from': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'date_to': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            })
        }
    
    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        if date_from and date_to:
            if date_from > date_to:
                raise forms.ValidationError("Start date must be before end date.")
            if date_to > timezone.now().date():
                raise forms.ValidationError("End date cannot be in the future.")
        
        return cleaned_data


class ReportTemplateForm(forms.ModelForm):
    """Form for report templates"""
    
    columns = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Enter columns as JSON array, e.g., ["name", "email", "phone"]'
        }),
        help_text="List of columns to include in the report (JSON format)"
    )
    
    default_filters = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Enter default filters as JSON object, e.g., {"status": "active"}'
        }),
        required=False,
        help_text="Default filter values (JSON format)"
    )
    
    class Meta:
        model = ReportTemplate
        fields = ['name', 'report_type', 'description', 'columns', 'default_filters']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Template name'
            }),
            'report_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Template description'
            })
        }
    
    def clean_columns(self):
        columns = self.cleaned_data.get('columns')
        try:
            import json
            parsed_columns = json.loads(columns)
            if not isinstance(parsed_columns, list):
                raise forms.ValidationError("Columns must be a JSON array.")
            return parsed_columns
        except json.JSONDecodeError:
            raise forms.ValidationError("Invalid JSON format for columns.")
    
    def clean_default_filters(self):
        default_filters = self.cleaned_data.get('default_filters')
        if not default_filters:
            return {}
        
        try:
            import json
            parsed_filters = json.loads(default_filters)
            if not isinstance(parsed_filters, dict):
                raise forms.ValidationError("Default filters must be a JSON object.")
            return parsed_filters
        except json.JSONDecodeError:
            raise forms.ValidationError("Invalid JSON format for default filters.")


class QuickReportForm(forms.Form):
    """Form for quick report generation"""
    
    REPORT_TYPES = [
        ('patients', 'Patients Report'),
        ('appointments', 'Appointments Report'),
        ('billing', 'Billing Report'),
        ('financial', 'Financial Report'),
    ]
    
    PERIODS = [
        ('today', 'Today'),
        ('week', 'This Week'),
        ('month', 'This Month'),
        ('quarter', 'This Quarter'),
        ('year', 'This Year'),
        ('custom', 'Custom Range'),
    ]
    
    report_type = forms.ChoiceField(
        choices=REPORT_TYPES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    period = forms.ChoiceField(
        choices=PERIODS,
        initial='month',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        period = cleaned_data.get('period')
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        if period == 'custom':
            if not date_from or not date_to:
                raise forms.ValidationError("Custom period requires both start and end dates.")
            if date_from > date_to:
                raise forms.ValidationError("Start date must be before end date.")
        
        return cleaned_data
