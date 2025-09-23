# opd/models.py
from django.db import models
from django.conf import settings

class OPD(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('emergency', 'Emergency'),
    )

    # Patient Information
    patient_name = models.CharField(max_length=100)
    patient_age = models.IntegerField()
    patient_gender = models.CharField(max_length=10, choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')])
    patient_phone = models.CharField(max_length=15)
    patient_email = models.EmailField(blank=True, null=True)

    # Medical Information
    symptoms = models.TextField()
    diagnosis = models.TextField(blank=True, null=True)
    prescription = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    # Visit Details
    visit_date = models.DateTimeField(auto_now_add=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    doctor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='opd_visits')
    department = models.CharField(max_length=50)
    fee = models.DecimalField(max_digits=10, decimal_places=2)
    is_paid = models.BooleanField(default=False)

    # Follow-up
    follow_up_date = models.DateField(blank=True, null=True)
    follow_up_notes = models.TextField(blank=True, null=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-visit_date']
        verbose_name = 'OPD'
        verbose_name_plural = 'OPD Records'

    def __str__(self):
        return f"{self.patient_name} - {self.visit_date.strftime('%Y-%m-%d')}"

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('opd:opd-detail', kwargs={'pk': self.pk})