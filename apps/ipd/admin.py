from django.contrib import admin
from .models import Room, Bed, IPDRecord, Treatment
# Register your models here.

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    #   list_display = ('__all__',)  # Display all fields
      list_display = [field.name for field in Room._meta.fields]  # or Patient._meta.fields
      def __str__(self):
        return self.name
@admin.register(Bed)
class BedAdmin(admin.ModelAdmin):
    #   list_display = ('__all__',)  # Display all fields
      list_display = [field.name for field in Bed._meta.fields]  # or Patient._meta.fields
      
      def __str__(self):
        return self.name
@admin.register(IPDRecord)
class IPDRecordAdmin(admin.ModelAdmin):
    #   list_display = ('__all__',)  # Display all fields
      list_display = [field.name for field in IPDRecord._meta.fields]  # or Patient._meta.fields
      def __str__(self):
        return self.name     

@admin.register(Treatment)
class TreatmentAdmin(admin.ModelAdmin):
    #   list_display = ('__all__',)  # Display all fields
      list_display = [field.name for field in Treatment._meta.fields]  # or Patient._meta.fields
      def __str__(self):
        return self.name           