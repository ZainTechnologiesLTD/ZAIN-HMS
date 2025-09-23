# doctors/api.py
from rest_framework import viewsets, status, serializers
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Doctor, DoctorSchedule, Prescription
from .serializers import (
    DoctorSerializer, DoctorCreateUpdateSerializer, 
    DoctorScheduleSerializer, PrescriptionSerializer
)
from apps.pharmacy.models import Medicine
from apps.patients.models import Patient
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_datetime

class DoctorViewSet(viewsets.ModelViewSet):
    queryset = Doctor.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name', 'last_name', 'email', 'phone_number']
    ordering_fields = ['last_name', 'first_name', 'date_of_birth']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return DoctorCreateUpdateSerializer
        return DoctorSerializer

    @action(detail=True, methods=['post'])
    def add_schedule(self, request, pk=None):
        doctor = self.get_object()
        serializer = DoctorScheduleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(doctor=doctor)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def schedules(self, request, pk=None):
        doctor = self.get_object()
        schedules = doctor.schedules.all()
        serializer = DoctorScheduleSerializer(schedules, many=True)
        return Response(serializer.data)

class DoctorScheduleViewSet(viewsets.ModelViewSet):
    queryset = DoctorSchedule.objects.all()
    serializer_class = DoctorScheduleSerializer

    def perform_create(self, serializer):
        doctor_id = self.kwargs.get('doctor_pk')
        doctor = get_object_or_404(Doctor, pk=doctor_id)
        if DoctorSchedule.objects.filter(
            doctor=doctor, 
            day_of_week=serializer.validated_data['day_of_week'],
            start_time=serializer.validated_data['start_time']
        ).exists():
            raise serializers.ValidationError("This doctor is already scheduled at this time.")
        serializer.save(doctor=doctor)

class PrescriptionViewSet(viewsets.ModelViewSet):
    queryset = Prescription.objects.all()
    serializer_class = PrescriptionSerializer

@api_view(['POST'])
def create_prescription(request):
    try:
        patient = Patient.objects.get(pk=request.data['patient_id'])
        doctor = Doctor.objects.get(pk=request.data['doctor_id'])
        date = parse_datetime(request.data.get('date'))
        if not date:
            raise ValueError("Invalid date format")

        prescription = Prescription.objects.create(
            patient=patient, doctor=doctor, date=date, 
            notes=request.data.get('notes')
        )

        for medicine_data in request.data.get('medicines', []):
            medicine = Medicine.objects.get(pk=medicine_data['medicine_id'])
            prescription.medicines.add(medicine, through_defaults={
                'dosage': medicine_data['dosage'],
                'frequency': medicine_data['frequency']
            })

        return Response({
            'message': 'Prescription created successfully',
            'prescription_data': {
                'id': prescription.id,
                'patient_id': patient.id,
                'doctor_id': doctor.id,
                'date': prescription.date.isoformat(),
                'notes': prescription.notes,
                'medicines': [
                    {
                        'id': item.medicine.id,
                        'name': item.medicine.name,
                        'dosage': item.dosage,
                        'frequency': item.frequency,
                    }
                    for item in prescription.medicines.through.objects.filter(prescription=prescription)
                ]
            }
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
