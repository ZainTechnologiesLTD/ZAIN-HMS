from django.db import models
from django.conf import settings  # Import settings to access AUTH_USER_MODEL

class Department(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

class Nurse(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other')
    ]

    SHIFT_CHOICES = [
        ('morning', 'Morning Shift'),
        ('afternoon', 'Afternoon Shift'),
        ('night', 'Night Shift')
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,  # Reference the correct user model
        on_delete=models.CASCADE, 
        related_name='nurse_profile'
    )
    employee_id = models.CharField(max_length=20, unique=True)
    department = models.ForeignKey(
        Department, on_delete=models.SET_NULL, 
        null=True, related_name='nurses'
    )
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    phone_number = models.CharField(max_length=15)
    address = models.TextField()
    qualifications = models.TextField()
    years_of_experience = models.PositiveIntegerField()
    shift = models.CharField(max_length=20, choices=SHIFT_CHOICES)
    joining_date = models.DateField()
    salary = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.employee_id})"

    class Meta:
        ordering = ['user__last_name', 'user__first_name']

class NurseSchedule(models.Model):
    nurse = models.ForeignKey(Nurse, on_delete=models.CASCADE, related_name='schedules')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nurse} - {self.date}"

    class Meta:
        ordering = ['-date', 'start_time']
        unique_together = ['nurse', 'date']

class NurseLeave(models.Model):
    LEAVE_TYPE_CHOICES = [
        ('sick', 'Sick Leave'),
        ('casual', 'Casual Leave'),
        ('annual', 'Annual Leave'),
        ('emergency', 'Emergency Leave')
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ]

    nurse = models.ForeignKey(Nurse, on_delete=models.CASCADE, related_name='leaves')
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPE_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Use AUTH_USER_MODEL here as well
        on_delete=models.SET_NULL, 
        null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nurse} - {self.leave_type} ({self.start_date} to {self.end_date})"

    class Meta:
        ordering = ['-start_date']
