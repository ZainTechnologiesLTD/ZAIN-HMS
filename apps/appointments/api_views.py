from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as filters
from .models import Appointment
from .serializers import AppointmentSerializer
from apps.doctors.models import Doctor, DoctorSchedule
from datetime import datetime

# Add a custom filter set
class AppointmentFilter(filters.FilterSet):
    appointment_date = filters.DateFilter(field_name='datetime', lookup_expr='date')
    status = filters.CharFilter()
    patient = filters.NumberFilter()
    doctor = filters.NumberFilter()

    class Meta:
        model = Appointment
        fields = ['appointment_date', 'status', 'patient', 'doctor']

class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = AppointmentFilter  # Use the custom filter set instead of filterset_fields

    # Rest of your code remains the same
    def check_doctor_availability(self, doctor, date, time):
        schedules = DoctorSchedule.objects.filter(doctor=doctor, day_of_week=date.weekday())
        for schedule in schedules:
            if schedule.is_available(date, time):
                return True
        return False

    def perform_create(self, serializer):
        doctor = serializer.validated_data.get('doctor')
        date = serializer.validated_data.get('date')
        time = serializer.validated_data.get('time')
        if self.check_doctor_availability(doctor, date, time):
            serializer.save()
        else:
            raise serializers.ValidationError("The doctor is not available at this time.")

    # Your action methods remain the same