from django.contrib import admin
from django.contrib.auth.models import Group, User
from apps.doctors.forms import DoctorAdminForm
from .models import Doctor, DoctorSchedule

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    form = DoctorAdminForm
    list_display = ('doctor_id', 'get_full_name', 'specialization', 'get_email', 'is_active')
    search_fields = ('user__first_name', 'user__last_name', 'user__email', 'specialization', 'doctor_id')
    list_filter = ('specialization', 'is_active')
    readonly_fields = ['created_at', 'updated_at']
    
    def get_full_name(self, obj):
        if obj.user:
            return f"{obj.user.first_name} {obj.user.last_name}"
        return "No User Assigned"
    get_full_name.short_description = 'Name'
    
    def get_email(self, obj):
        if obj.user:
            return obj.user.email
        return "No Email"
    get_email.short_description = 'Email'
    
    def get_queryset(self, request):
        """Override to ensure proper select_related for performance"""
        queryset = super().get_queryset(request)
        return queryset.select_related('user')

    def save_model(self, request, obj, form, change):
        if not obj.pk:  # Only for new doctors
            # Create User
            user = User.objects.create_user(
                username=form.cleaned_data['email'],
                email=form.cleaned_data['email'],
                password='defaultpassword123',  # Set a default password or customize this logic
            )
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.save()

            # Assign to Doctor group
            doctor_group, _ = Group.objects.get_or_create(name='Doctor')
            user.groups.add(doctor_group)
            obj.user = user

        super().save_model(request, obj, form, change)

@admin.register(DoctorSchedule)
class DoctorScheduleAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'day_of_week', 'start_time', 'end_time')
    search_fields = ('doctor__user__first_name', 'doctor__user__last_name', 'doctor__doctor_id')
    list_filter = ('day_of_week',)
    
    def get_queryset(self, request):
        """Override to ensure proper select_related for performance"""
        queryset = super().get_queryset(request)
        return queryset.select_related('doctor', 'doctor__user')
