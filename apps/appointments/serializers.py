# appointments/serializers.py
from rest_framework import serializers
from .models import Appointment
from doctors.models import Doctor


class AppointmentSerializer(serializers.ModelSerializer):
    doctor = serializers.PrimaryKeyRelatedField(queryset=Doctor.objects.all())

    class Meta:
        model = Appointment
        fields = '__all__'

    def validate(self, data):
        """
        Check if the doctor is available before saving the appointment.
        """
        doctor = data.get('doctor')
        date = data.get('date')
        time = data.get('time')

        # Perform availability check before proceeding
        if doctor and date and time:
            if not self.context['view'].check_doctor_availability(doctor, date, time):
                raise serializers.ValidationError("The doctor is not available at this time.")
        
        return data
