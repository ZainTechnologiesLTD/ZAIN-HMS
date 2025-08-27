# apps/accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    """Enhanced admin for CustomUser with hospital management features"""
    
    list_display = ('username', 'email', 'first_name', 'last_name', 'hospital', 'role', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('hospital', 'role', 'is_staff', 'is_active', 'date_joined', 'gender')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'employee_id')
    ordering = ('-date_joined',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Hospital Information', {
            'fields': ('hospital', 'role', 'employee_id', 'phone', 'address')
        }),
        ('Personal Information', {
            'fields': ('date_of_birth', 'gender', 'emergency_contact')
        }),
        ('Hospital Access', {
            'fields': ('is_superadmin', 'is_active_staff')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Hospital Role', {
            'fields': ('hospital', 'role', 'email', 'first_name', 'last_name')
        }),
    )
    
    def get_form(self, request, obj=None, **kwargs):
        """Customize form based on user permissions"""
        form = super().get_form(request, obj, **kwargs)
        
        # Only superusers can create superadmins
        if not request.user.is_superuser:
            if 'role' in form.base_fields:
                # Remove SUPERADMIN option for non-superusers
                choices = [choice for choice in CustomUser.ROLE_CHOICES if choice[0] != 'SUPERADMIN']
                form.base_fields['role'].choices = choices
                
        return form
    
    def save_model(self, request, obj, form, change):
        """Set appropriate permissions when saving user and ensure user is saved to default DB."""
        # Ensure the user record is always persisted to the shared default database
        # to avoid accidental writes into tenant-specific DBs.
        try:
            # Adjust flags before saving
            if obj.role == 'SUPERADMIN':
                obj.is_staff = True
                obj.is_superuser = True
            else:
                obj.is_staff = False
                obj.is_superuser = False

            # Save using the default DB explicitly
            obj.save(using='default')
        except Exception:
            # Fallback: call the base implementation to preserve behavior
            super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        """Filter users based on permissions"""
        # Force admin list reads to use the default DB so the shared user table
        # is always queried from the main database.
        qs = super().get_queryset(request).using('default')
        if not request.user.is_superuser:
            # Non-superusers can't see superadmins
            qs = qs.exclude(role='SUPERADMIN')
        return qs
    
    actions = ['make_admin', 'make_doctor', 'make_nurse', 'activate_users', 'deactivate_users']
    
    def make_admin(self, request, queryset):
        """Convert selected users to hospital administrators"""
        updated = queryset.update(role='HOSPITAL_ADMIN', is_staff=False)
        self.message_user(request, f'{updated} users were successfully made hospital administrators.')
    make_admin.short_description = 'Make selected users hospital administrators'
    
    def make_doctor(self, request, queryset):
        """Convert selected users to doctors"""
        updated = queryset.update(role='DOCTOR')
        self.message_user(request, f'{updated} users were successfully made doctors.')
    make_doctor.short_description = 'Make selected users doctors'
    
    def make_nurse(self, request, queryset):
        """Convert selected users to nurses"""
        updated = queryset.update(role='NURSE')
        self.message_user(request, f'{updated} users were successfully made nurses.')
    make_nurse.short_description = 'Make selected users nurses'
    
    def activate_users(self, request, queryset):
        """Activate selected users"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} users were successfully activated.')
    activate_users.short_description = 'Activate selected users'
    
    def deactivate_users(self, request, queryset):
        """Deactivate selected users"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} users were successfully deactivated.')
    deactivate_users.short_description = 'Deactivate selected users'
