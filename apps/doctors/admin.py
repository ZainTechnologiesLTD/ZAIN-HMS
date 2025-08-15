from django.contrib import admin
from django.contrib.auth.models import Group, User
from doctors.forms import DoctorAdminForm
from .models import Doctor, DoctorSchedule

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    form = DoctorAdminForm
    list_display = ('doctor_id', 'get_full_name', 'specialization', 'get_email', 'is_active')
    search_fields = ('user__first_name', 'user__last_name', 'user__email', 'specialization')
    list_filter = ('specialization', 'is_active')
    
    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    get_full_name.short_description = 'Name'
    
    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'

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
    search_fields = ('doctor__user__first_name', 'doctor__user__last_name')
    list_filter = ('day_of_week', 'doctor')
