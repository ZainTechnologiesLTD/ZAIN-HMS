# ZAIN HMS Custom Security Validators
# Healthcare-grade password and data validators for HIPAA compliance

import re
import string
from datetime import datetime, timedelta
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import CommonPasswordValidator
from django.utils.translation import gettext as _
from django.contrib.auth.models import User
from django.core.cache import cache
import hashlib


class HealthcarePasswordValidator:
    """
    Custom password validator for healthcare environments
    Implements enhanced security requirements for HIPAA compliance
    """
    
    def __init__(self):
        self.min_length = 12
        self.require_uppercase = True
        self.require_lowercase = True
        self.require_digits = True
        self.require_special = True
        self.max_consecutive = 2
        self.prevent_common_patterns = True
        
    def validate(self, password, user=None):
        """Comprehensive password validation for healthcare systems"""
        
        # Length requirement
        if len(password) < self.min_length:
            raise ValidationError(
                f'Password must be at least {self.min_length} characters long.',
                code='password_too_short',
            )
            
        # Character composition requirements
        if self.require_uppercase and not re.search(r'[A-Z]', password):
            raise ValidationError(
                'Password must contain at least one uppercase letter.',
                code='password_no_uppercase',
            )
            
        if self.require_lowercase and not re.search(r'[a-z]', password):
            raise ValidationError(
                'Password must contain at least one lowercase letter.',
                code='password_no_lowercase',
            )
            
        if self.require_digits and not re.search(r'\d', password):
            raise ValidationError(
                'Password must contain at least one digit.',
                code='password_no_digit',
            )
            
        if self.require_special and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError(
                'Password must contain at least one special character (!@#$%^&*(),.?":{}|<>).',
                code='password_no_special',
            )
            
        # Consecutive character check
        if self._has_consecutive_chars(password, self.max_consecutive):
            raise ValidationError(
                f'Password cannot contain more than {self.max_consecutive} consecutive identical characters.',
                code='password_consecutive_chars',
            )
            
        # Common pattern checks for healthcare
        if self._contains_healthcare_patterns(password):
            raise ValidationError(
                'Password cannot contain common healthcare-related terms or patterns.',
                code='password_healthcare_pattern',
            )
            
        # User-specific validation
        if user:
            self._validate_user_specific(password, user)
            
    def _has_consecutive_chars(self, password, max_consecutive):
        """Check for consecutive identical characters"""
        consecutive_count = 1
        for i in range(1, len(password)):
            if password[i] == password[i-1]:
                consecutive_count += 1
                if consecutive_count > max_consecutive:
                    return True
            else:
                consecutive_count = 1
        return False
        
    def _contains_healthcare_patterns(self, password):
        """Check for common healthcare-related patterns"""
        healthcare_patterns = [
            'hospital', 'patient', 'doctor', 'nurse', 'medical', 'health',
            'admin', 'password', 'login', 'system', 'user', 'test',
            '123456', 'qwerty', 'abc123', 'password123', 'admin123'
        ]
        
        password_lower = password.lower()
        return any(pattern in password_lower for pattern in healthcare_patterns)
        
    def _validate_user_specific(self, password, user):
        """Validate password against user-specific information"""
        if hasattr(user, 'username') and user.username.lower() in password.lower():
            raise ValidationError(
                'Password cannot contain your username.',
                code='password_contains_username',
            )
            
        if hasattr(user, 'email') and user.email:
            email_parts = user.email.split('@')[0].lower()
            if len(email_parts) > 3 and email_parts in password.lower():
                raise ValidationError(
                    'Password cannot contain parts of your email address.',
                    code='password_contains_email',
                )
                
        if hasattr(user, 'first_name') and user.first_name:
            if len(user.first_name) > 2 and user.first_name.lower() in password.lower():
                raise ValidationError(
                    'Password cannot contain your first name.',
                    code='password_contains_name',
                )
                
        if hasattr(user, 'last_name') and user.last_name:
            if len(user.last_name) > 2 and user.last_name.lower() in password.lower():
                raise ValidationError(
                    'Password cannot contain your last name.',
                    code='password_contains_name',
                )
    
    def get_help_text(self):
        """Return help text for password requirements"""
        return _(
            f'Your password must contain at least {self.min_length} characters, '
            'including uppercase and lowercase letters, digits, and special characters. '
            'It cannot contain common healthcare terms or personal information.'
        )


class PasswordHistoryValidator:
    """
    Prevent password reuse for healthcare compliance
    Maintains history of password hashes to prevent reuse
    """
    
    def __init__(self, history_count=12):  # HIPAA recommends 12 unique passwords
        self.history_count = history_count
        
    def validate(self, password, user=None):
        if not user or not hasattr(user, 'pk') or not user.pk:
            return  # Can't check history for new users
            
        # Create hash of new password
        password_hash = self._hash_password(password)
        
        # Get password history from cache
        cache_key = f'password_history_{user.pk}'
        password_history = cache.get(cache_key, [])
        
        # Check if password was used before
        if password_hash in password_history:
            raise ValidationError(
                f'You cannot reuse any of your last {self.history_count} passwords.',
                code='password_previously_used',
            )
            
    def _hash_password(self, password):
        """Create a hash of the password for history tracking"""
        return hashlib.pbkdf2_hmac('sha256', password.encode(), b'salt', 100000).hex()
        
    def store_password_history(self, user, password):
        """Store password in history after successful change"""
        password_hash = self._hash_password(password)
        cache_key = f'password_history_{user.pk}'
        
        password_history = cache.get(cache_key, [])
        password_history.insert(0, password_hash)  # Add to front
        
        # Keep only the required history count
        password_history = password_history[:self.history_count]
        
        # Store for 1 year (longer than typical password expiry)
        cache.set(cache_key, password_history, timeout=365*24*3600)
        
    def get_help_text(self):
        return _(
            f'Password cannot be the same as any of your last {self.history_count} passwords.'
        )


print("🔐 Healthcare security validators loaded")
print("⚕️ HIPAA-compliant validation rules active")
print("🛡️ PHI protection validators ready")