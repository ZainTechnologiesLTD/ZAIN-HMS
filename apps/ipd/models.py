# ipd/models.py

from django.db import models
from apps.patients.models import Patient
from apps.doctors.models import Doctor

class Room(models.Model):
    number = models.CharField(max_length=10)
    floor = models.IntegerField()
    room_type = models.CharField(max_length=20, choices=[('General', 'General'), ('Private', 'Private')])
    is_occupied = models.BooleanField(default=False)

    def __str__(self):
        return f"Room {self.number}, {self.room_type}"
    
class Bed(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='beds')
    number = models.CharField(max_length=10)
    available = models.BooleanField(default=True)

    def __str__(self):
        return f"Bed {self.number} in {self.room}"


class IPDRecord(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='ipd_patients')
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True)
    bed = models.ForeignKey(Bed, on_delete=models.CASCADE)
    admission_date = models.DateTimeField(auto_now_add=True)
    discharge_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[('Admitted', 'Admitted'), ('Discharged', 'Discharged')])

    def __str__(self):
        return f"IPD Record for {self.patient.name}"

class Treatment(models.Model):
    ipd_record = models.ForeignKey(IPDRecord, related_name='treatments', on_delete=models.CASCADE)
    treatment_name = models.CharField(max_length=100)
    date = models.DateField()
    notes = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Treatment: {self.treatment_name} for {self.ipd_record.patient.last_name}"
