# appointments/admin.py

from django.contrib import admin
from .models import Appointment, Prescription


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
   
      list_display = ['patient', 'doctor', 'appointment_type', 'date_time', 'status', 'fee']
      list_filter = ['status', 'appointment_type', 'doctor']  # Replace with valid fields
      search_fields = ['patient__first_name', 'patient__last_name', 'doctor__last_name']
      ordering = ['date_time']
      def __str__(self):
        return self.name
      
@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ['appointment', 'date_time', 'notes']
    # Display all fields
    def __str__(self):
        return self.name
    