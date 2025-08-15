from django.contrib import admin
from .models import LabTest, LabResult

@admin.register(LabTest)
class LabTestAdmin(admin.ModelAdmin):
    list_display = [field.name for field in LabTest._meta.fields]  
    search_fields = ('patient__name', 'test_name', 'description')
    list_filter = ('test_name', 'created_at')
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
  
@admin.register(LabResult)
class LabResultAdmin(admin.ModelAdmin):
    list_display = [field.name for field in LabResult._meta.fields]  
    list_filter = ('test', 'date_performed')
    search_fields = ('patient__name', 'test__name', 'technician')  # Assuming patient model has a 'name' field
    date_hierarchy = 'date_performed'
    ordering = ['-date_performed']
 