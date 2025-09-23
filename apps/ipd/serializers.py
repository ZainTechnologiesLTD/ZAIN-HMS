from rest_framework import serializers  
from .models import Room, IPDRecord, Treatment, Bed

class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ['id', 'number', 'floor', 'room_type', 'is_occupied']

class BedSerializer(serializers.ModelSerializer):
    room = RoomSerializer(read_only=True)  # Include room info in bed details

    class Meta:
        model = Bed
        fields = ['id', 'number', 'available', 'room']

class TreatmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Treatment
        fields = ['id', 'treatment_name', 'date', 'notes']

class IPDRecordSerializer(serializers.ModelSerializer):
    patient_name = serializers.ReadOnlyField(source='patient.last_name')
    doctor_name = serializers.ReadOnlyField(source='doctor.last_name')
    treatments = TreatmentSerializer(many=True, read_only=True)
    room = RoomSerializer(read_only=True)  # Serialize room details
    bed = BedSerializer(read_only=True)    # Serialize bed details
    admission_date = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = IPDRecord
        fields = ['id', 'patient', 'doctor', 'room', 'bed', 'admission_date', 'discharge_date', 'status', 'patient_name', 'doctor_name', 'treatments']
