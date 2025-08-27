from django.contrib import admin
from .models import Patient

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('patient_id', 'get_full_name', 'phone', 'email', 'date_of_birth', 'registration_date')
    search_fields = ('patient_id', 'first_name', 'last_name', 'phone', 'email')
    list_filter = ('gender', 'blood_group', 'registration_date', 'is_active', 'is_vip')
    readonly_fields = ['patient_id', 'registration_date', 'last_visit']
    ordering = ['-registration_date']
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    get_full_name.short_description = 'Name'