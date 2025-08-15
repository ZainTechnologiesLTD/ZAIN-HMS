from django.contrib import admin

from .models import Medicine, PharmaceuticalBill, BillItem

@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    #   list_display = ('__all__',)  # Display all fields
      list_display = [field.name for field in Medicine._meta.fields]  # or Patient._meta.fields
      def __str__(self):
        return self.name
@admin.register(PharmaceuticalBill)
class PharmaceuticalBillAdmin(admin.ModelAdmin):
    #   list_display = ('__all__',)  # Display all fields
      list_display = [field.name for field in PharmaceuticalBill._meta.fields]  # or Patient._meta.fields
      
      def __str__(self):
        return self.name
@admin.register(BillItem)
class BillItemAdmin(admin.ModelAdmin):
    #   list_display = ('__all__',)  # Display all fields
      list_display = [field.name for field in BillItem._meta.fields]  # or Patient._meta.fields
      def __str__(self):
        return self.name     