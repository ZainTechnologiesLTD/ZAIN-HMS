# apps/core/utils/serial_number.py
from django.db import models, transaction
from django.utils import timezone
from django.core.cache import cache
import threading

_lock = threading.Lock()

class SerialNumberGenerator:
    """Utility class for generating sequential serial numbers"""
    
    DOCUMENT_TYPES = {
        'appointment': 'APT',
        'lab_order': 'LAB', 
        'radiology_order': 'RAD',
        'bill': 'BIL',
        'patient': 'PAT',
        'doctor': 'DOC',
        'prescription': 'PRE',
        'report': 'RPT'
    }
    
    @classmethod
    def generate_serial_number(cls, document_type, hospital_code=None):
        """
        Generate a sequential serial number for a document type
        
        Args:
            document_type (str): Type of document ('appointment', 'lab_order', etc.)
            hospital_code (str): Optional hospital code
            
        Returns:
            str: Generated serial number in format PREFIX-YYYY-NNNNNN
        """
        with _lock:
            prefix = cls.DOCUMENT_TYPES.get(document_type, 'DOC')
            year = timezone.now().year
            
            # Create cache key for atomic increment
            cache_key = f"serial_{hospital_code or 'default'}_{document_type}_{year}"
            
            # Get current number from cache or initialize
            current_number = cache.get(cache_key, 0)
            new_number = current_number + 1
            
            # Set cache with 1 year expiry
            cache.set(cache_key, new_number, 365 * 24 * 60 * 60)
            
            # Format: PREFIX-YYYY-NNNNNN
            if hospital_code:
                return f"{hospital_code}-{prefix}-{year}-{new_number:06d}"
            else:
                return f"{prefix}-{year}-{new_number:06d}"
    
    @classmethod
    def get_next_number(cls, document_type, hospital_code=None):
        """Get the next number that would be generated without incrementing"""
        prefix = cls.DOCUMENT_TYPES.get(document_type, 'DOC')
        year = timezone.now().year
        
        cache_key = f"serial_{hospital_code or 'default'}_{document_type}_{year}"
        current_number = cache.get(cache_key, 0)
        next_number = current_number + 1
        
        if hospital_code:
            return f"{hospital_code}-{prefix}-{year}-{next_number:06d}"
        else:
            return f"{prefix}-{year}-{next_number:06d}"
    
    @classmethod
    def reset_counter(cls, document_type, hospital_code=None, year=None):
        """Reset counter for a document type (admin use only)"""
        year = year or timezone.now().year
        cache_key = f"serial_{hospital_code or 'default'}_{document_type}_{year}"
        cache.delete(cache_key)
    
    @classmethod
    def set_counter(cls, document_type, number, hospital_code=None, year=None):
        """Set counter to a specific number (admin use only)"""
        year = year or timezone.now().year
        cache_key = f"serial_{hospital_code or 'default'}_{document_type}_{year}"
        cache.set(cache_key, number, 365 * 24 * 60 * 60)


class SerialNumberMixin(models.Model):
    """Mixin to add serial number functionality to models"""
    
    serial_number = models.CharField(
        max_length=50, 
        unique=True, 
        blank=True,
        help_text="Auto-generated serial number"
    )
    
    class Meta:
        abstract = True
    
    def generate_serial_number(self, document_type, hospital_code=None):
        """Generate and assign serial number"""
        if not self.serial_number:
            self.serial_number = SerialNumberGenerator.generate_serial_number(
                document_type, 
                hospital_code
            )
    
    def save(self, *args, **kwargs):
        # Auto-generate serial number if not set
        if not self.serial_number and hasattr(self, 'SERIAL_TYPE'):
            hospital_code = None
            if hasattr(self, 'hospital') and self.hospital:
                hospital_code = getattr(self.hospital, 'code', None)
            self.generate_serial_number(self.SERIAL_TYPE, hospital_code)
        
        super().save(*args, **kwargs)


def get_serial_number_stats(hospital_code=None):
    """Get statistics about serial number usage"""
    stats = {}
    year = timezone.now().year
    
    for doc_type, prefix in SerialNumberGenerator.DOCUMENT_TYPES.items():
        cache_key = f"serial_{hospital_code or 'default'}_{doc_type}_{year}"
        current_number = cache.get(cache_key, 0)
        stats[doc_type] = {
            'prefix': prefix,
            'current_number': current_number,
            'next_number': current_number + 1,
            'year': year
        }
    
    return stats
