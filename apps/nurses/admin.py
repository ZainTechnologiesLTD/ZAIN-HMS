from django.contrib import admin
from .models import Nurse, NurseSchedule, NurseLeave

@admin.register(Nurse)
class NurseAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'get_full_name', 'department', 'shift', 'phone_number', 'is_active')
    list_filter = ('department', 'shift', 'is_active', 'joining_date')
    search_fields = ('user__first_name', 'user__last_name', 'employee_id', 'phone_number')
    ordering = ('user__last_name', 'user__first_name')
    date_hierarchy = 'joining_date'
    
    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'Name'
    get_full_name.admin_order_field = 'user__last_name'

    fieldsets = (
        ('Personal Information', {
            'fields': (('user', 'employee_id'), ('date_of_birth', 'gender'), 
                      'phone_number', 'address')
        }),
        ('Professional Information', {
            'fields': (('department', 'shift'), ('qualifications', 'years_of_experience'),
                      'joining_date', 'salary', 'is_active')
        }),
    )

@admin.register(NurseSchedule)
class NurseScheduleAdmin(admin.ModelAdmin):
    list_display = ('nurse', 'date', 'start_time', 'end_time')
    list_filter = ('date',)
    search_fields = ('nurse__user__first_name', 'nurse__user__last_name', 'nurse__employee_id')
    ordering = ('-date', 'start_time')
    date_hierarchy = 'date'

    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return ('nurse', 'date')
        return ()

@admin.register(NurseLeave)
class NurseLeaveAdmin(admin.ModelAdmin):
    list_display = ('nurse', 'leave_type', 'start_date', 'end_date', 'status', 'approved_by')
    list_filter = ('leave_type', 'status', 'start_date')
    search_fields = ('nurse__user__first_name', 'nurse__user__last_name', 'nurse__employee_id')
    ordering = ('-start_date',)
    date_hierarchy = 'start_date'
    
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.status != 'pending':  # if leave is already approved/rejected
            return ('nurse', 'leave_type', 'start_date', 'end_date', 'reason')
        return ()