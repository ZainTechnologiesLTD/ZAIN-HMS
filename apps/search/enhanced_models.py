# Enhanced Universal Search System
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from apps.accounts.models import CustomUser as User
from apps.patients.models import Patient
from apps.doctors.models import Doctor
from apps.appointments.models import Appointment
import uuid


class SearchableItem(models.Model):
    """Universal search index for all searchable content"""
    SEARCH_CATEGORIES = [
        ('patient', 'Patient'),
        ('doctor', 'Doctor'),
        ('nurse', 'Nurse'), 
        ('staff', 'Staff'),
        ('appointment', 'Appointment'),
        ('lab_test', 'Laboratory Test'),
        ('medicine', 'Medicine'),
        ('diagnosis', 'Diagnosis'),
        ('procedure', 'Medical Procedure'),
    ]
    
    # Universal identifier
    search_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # Search metadata
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, choices=SEARCH_CATEGORIES)
    keywords = models.TextField(blank=True, help_text="Comma-separated search keywords")
    
    # Generic foreign key to link to any model
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Search relevance and priority
    priority = models.IntegerField(default=1, help_text="Higher numbers = higher priority in search")
    is_active = models.BooleanField(default=True)
    
    # Tracking
    search_count = models.PositiveIntegerField(default=0)
    last_searched = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-priority', '-search_count', 'title']
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['title']),
            models.Index(fields=['priority', '-search_count']),
        ]
        
    def __str__(self):
        return f"{self.category.title()}: {self.title}"
        
    def increment_search_count(self):
        """Increment search count for analytics"""
        from django.utils import timezone
        self.search_count += 1
        self.last_searched = timezone.now()
        self.save(update_fields=['search_count', 'last_searched'])


class QuickSearchSuggestion(models.Model):
    """Pre-defined search suggestions for faster access"""
    title = models.CharField(max_length=100)
    search_query = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=SearchableItem.SEARCH_CATEGORIES)
    icon = models.CharField(max_length=50, blank=True, help_text="Font Awesome icon class")
    
    # Usage tracking
    usage_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    # Admin settings
    is_featured = models.BooleanField(default=False)
    display_order = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['display_order', '-usage_count', 'title']
        
    def __str__(self):
        return self.title


class UserSearchHistory(models.Model):
    """Track user search history for personalization"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='search_history')
    search_query = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=SearchableItem.SEARCH_CATEGORIES, blank=True)
    result_count = models.PositiveIntegerField(default=0)
    
    # Tracking
    searched_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        ordering = ['-searched_at']
        indexes = [
            models.Index(fields=['user', '-searched_at']),
            models.Index(fields=['search_query']),
        ]
        
    def __str__(self):
        return f"{self.user.username}: {self.search_query}"
