# Phone number validation and formatting utilities
import re
import phonenumbers
from phonenumbers import NumberParseException
from django.core.exceptions import ValidationError


class PhoneNumberValidator:
    """Validate and format phone numbers for international messaging"""
    
    def __init__(self, default_country='US'):
        self.default_country = default_country
    
    def clean_phone(self, phone_str):
        """Remove all non-numeric characters except +"""
        if not phone_str:
            return ''
        return re.sub(r'[^0-9+]', '', str(phone_str))
    
    def validate_e164(self, phone_str):
        """Validate phone number in E.164 format"""
        try:
            # Parse the number
            parsed = phonenumbers.parse(phone_str, self.default_country)
            
            # Validate the number
            if not phonenumbers.is_valid_number(parsed):
                return False, "Invalid phone number"
            
            # Format to E.164
            e164 = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
            
            return True, e164
            
        except NumberParseException as e:
            return False, f"Phone parse error: {e}"
        except Exception as e:
            return False, f"Validation error: {e}"
    
    def format_for_whatsapp(self, phone_str):
        """Format phone number for WhatsApp (no + prefix)"""
        is_valid, result = self.validate_e164(phone_str)
        if is_valid:
            # Remove + for WhatsApp wa.me links
            return result.lstrip('+')
        return None
    
    def format_for_display(self, phone_str):
        """Format phone number for display"""
        try:
            parsed = phonenumbers.parse(phone_str, self.default_country)
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
        except:
            return phone_str
    
    def get_country_code(self, phone_str):
        """Extract country code from phone number"""
        try:
            parsed = phonenumbers.parse(phone_str, self.default_country)
            return parsed.country_code
        except:
            return None


# Django form field
from django import forms

class PhoneNumberField(forms.CharField):
    """Custom phone number form field with validation"""
    
    def __init__(self, *args, **kwargs):
        self.country = kwargs.pop('country', 'US')
        super().__init__(*args, **kwargs)
        self.widget.attrs.update({
            'placeholder': '+1234567890',
            'pattern': r'^\+[1-9]\d{1,14}$',
            'title': 'Enter phone number in international format (+1234567890)'
        })
    
    def validate(self, value):
        super().validate(value)
        
        if value:
            validator = PhoneNumberValidator(self.country)
            is_valid, message = validator.validate_e164(value)
            
            if not is_valid:
                raise ValidationError(message)
    
    def clean(self, value):
        value = super().clean(value)
        
        if value:
            validator = PhoneNumberValidator(self.country)
            is_valid, result = validator.validate_e164(value)
            
            if is_valid:
                return result
            else:
                raise ValidationError(result)
        
        return value


# Template filter for phone formatting
from django import template

register = template.Library()

@register.filter
def format_phone(phone_str, format_type='display'):
    """Format phone number in template"""
    if not phone_str:
        return ''
    
    validator = PhoneNumberValidator()
    
    if format_type == 'whatsapp':
        return validator.format_for_whatsapp(phone_str) or phone_str
    elif format_type == 'display':
        return validator.format_for_display(phone_str)
    else:
        return phone_str
