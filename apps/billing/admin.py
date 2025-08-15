from django.contrib import admin
from .models import Bill

@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Bill._meta.fields]  # Display all fields in the admin interface
