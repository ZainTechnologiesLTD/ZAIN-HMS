# apps/core/validators.py
import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class PasswordComplexityValidator:
    """
    Validate that the password contains at least one uppercase letter,
    one lowercase letter, one digit, and one special character.
    """
    
    def validate(self, password, user=None):
        errors = []
        
        if not re.search(r'[A-Z]', password):
            errors.append(_('Password must contain at least one uppercase letter.'))
        
        if not re.search(r'[a-z]', password):
            errors.append(_('Password must contain at least one lowercase letter.'))
        
        if not re.search(r'\d', password):
            errors.append(_('Password must contain at least one digit.'))
        
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:"\\|,.<>\/?]', password):
            errors.append(_('Password must contain at least one special character.'))
        
        if errors:
            raise ValidationError(errors)
    
    def get_help_text(self):
        return _(
            'Your password must contain at least one uppercase letter, '
            'one lowercase letter, one digit, and one special character.'
        )


class PhoneNumberValidator:
    """Validate phone number format"""
    
    def __init__(self, country_code=None):
        self.country_code = country_code
    
    def __call__(self, value):
        # Remove spaces, dashes, and parentheses
        cleaned = re.sub(r'[\s\-\(\)]', '', value)
        
        # Check for valid phone number pattern
        if not re.match(r'^\+?[\d]{10,15}$', cleaned):
            raise ValidationError(
                _('Enter a valid phone number with 10-15 digits.'),
                code='invalid_phone'
            )


class MedicalRecordNumberValidator:
    """Validate medical record number format"""
    
    def __call__(self, value):
        # Check for alphanumeric format with optional hyphens
        if not re.match(r'^[A-Z0-9\-]{6,20}$', value.upper()):
            raise ValidationError(
                _('Medical record number must be 6-20 characters long and contain only letters, numbers, and hyphens.'),
                code='invalid_mrn'
            )


class LicenseNumberValidator:
    """Validate medical license number format"""
    
    def __call__(self, value):
        # Check for alphanumeric format
        if not re.match(r'^[A-Z0-9]{6,15}$', value.upper()):
            raise ValidationError(
                _('License number must be 6-15 characters long and contain only letters and numbers.'),
                code='invalid_license'
            )


class DrugCodeValidator:
    """Validate drug/medication code format"""
    
    def __call__(self, value):
        # Check for standard drug code format
        if not re.match(r'^[A-Z0-9\-]{4,12}$', value.upper()):
            raise ValidationError(
                _('Drug code must be 4-12 characters long and contain only letters, numbers, and hyphens.'),
                code='invalid_drug_code'
            )


class BloodPressureValidator:
    """Validate blood pressure format (systolic/diastolic)"""
    
    def __call__(self, value):
        if not re.match(r'^\d{2,3}/\d{2,3}$', value):
            raise ValidationError(
                _('Blood pressure must be in format: systolic/diastolic (e.g., 120/80)'),
                code='invalid_bp'
            )
        
        parts = value.split('/')
        systolic = int(parts[0])
        diastolic = int(parts[1])
        
        if not (60 <= systolic <= 300) or not (40 <= diastolic <= 200):
            raise ValidationError(
                _('Blood pressure values are outside normal range.'),
                code='invalid_bp_range'
            )


class TemperatureValidator:
    """Validate temperature values"""
    
    def __init__(self, unit='celsius'):
        self.unit = unit
    
    def __call__(self, value):
        try:
            temp = float(value)
            if self.unit == 'celsius':
                if not (25.0 <= temp <= 45.0):
                    raise ValidationError(
                        _('Temperature must be between 25°C and 45°C.'),
                        code='invalid_temp'
                    )
            elif self.unit == 'fahrenheit':
                if not (77.0 <= temp <= 113.0):
                    raise ValidationError(
                        _('Temperature must be between 77°F and 113°F.'),
                        code='invalid_temp'
                    )
        except (ValueError, TypeError):
            raise ValidationError(
                _('Enter a valid temperature value.'),
                code='invalid_temp_format'
            )


class HeartRateValidator:
    """Validate heart rate values"""
    
    def __call__(self, value):
        try:
            hr = int(value)
            if not (30 <= hr <= 220):
                raise ValidationError(
                    _('Heart rate must be between 30 and 220 BPM.'),
                    code='invalid_heart_rate'
                )
        except (ValueError, TypeError):
            raise ValidationError(
                _('Enter a valid heart rate value.'),
                code='invalid_heart_rate_format'
            )


class InsurancePolicyValidator:
    """Validate insurance policy number format"""
    
    def __call__(self, value):
        # Remove spaces and hyphens
        cleaned = re.sub(r'[\s\-]', '', value)
        
        # Check for alphanumeric format
        if not re.match(r'^[A-Z0-9]{8,20}$', cleaned.upper()):
            raise ValidationError(
                _('Insurance policy number must be 8-20 characters long and contain only letters and numbers.'),
                code='invalid_policy'
            )
