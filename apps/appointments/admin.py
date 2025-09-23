# appointments/admin.py

from django.contrib import admin
from .models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['appointment_number', 'patient', 'doctor', 'appointment_date', 'appointment_time', 'status', 'consultation_fee']
    list_filter = ['status']  # Removed 'appointment_type' filter due to field removal
    search_fields = ['patient__first_name', 'patient__last_name', 'doctor__user__first_name', 'doctor__user__last_name']
    ordering = ['appointment_date', 'appointment_time']
    readonly_fields = ['appointment_number', 'created_at', 'updated_at']
    
    def get_queryset(self, request):
        """Override to ensure proper select_related for performance"""
        queryset = super().get_queryset(request)
        return queryset.select_related('patient', 'doctor', 'doctor__user', 'created_by')
    