from django.contrib import admin

# Register your models here.
# patients/admin.py

from .models import Patient

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    #   list_display = ('__all__',)  # Display all fields
      list_display = [field.name for field in Patient._meta.fields]  # or Patient._meta.fields
      def __str__(self):
        return self.name