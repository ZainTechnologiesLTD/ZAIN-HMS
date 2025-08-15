from django.db import models
from patients.models import Patient
from doctors.models import Doctor

class LabTest(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='lab_tests')
    referred_doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='lab_tests')
    test_name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.test_name} - {self.created_at}"

class LabResult(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='lab_results')
    test = models.ForeignKey(LabTest, on_delete=models.CASCADE, related_name='lab_results')
    result = models.TextField()
    parameters = models.JSONField()
    date_performed = models.DateTimeField(auto_now_add=True)
    technician = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.patient} - {self.test} - {self.date_performed}"