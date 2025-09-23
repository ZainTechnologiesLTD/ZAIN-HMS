from rest_framework import serializers
from .models import Doctor, DoctorSchedule, Prescription

class DoctorScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorSchedule
        fields = ['doctor', 'day_of_week', 'start_time', 'end_time']

class DoctorSerializer(serializers.ModelSerializer):
    schedules = DoctorScheduleSerializer(many=True, read_only=True)

    class Meta:
        model = Doctor
        fields = [
            'id', 'doctor_id', 'first_name', 'last_name', 'specialization',
            'license_number', 'phone_number', 'email', 'date_of_birth',
            'address', 'image', 'joining_date', 'is_active', 'schedules'
        ]

class DoctorCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = [
            'first_name', 'last_name', 'specialization', 'license_number',
            'phone_number', 'email', 'date_of_birth', 'address', 'joining_date',
            'is_active'
        ]

class PrescriptionSerializer(serializers.ModelSerializer):
    date = serializers.DateTimeField(format='%Y-%m-%dT%H:%M:%S')

    class Meta:
        model = Prescription
        fields = ['id', 'patient_id', 'doctor_id', 'date', 'notes', 'medicines']
