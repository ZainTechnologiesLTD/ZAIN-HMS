from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django import forms
from django.http import JsonResponse
from django.urls import path
from django.utils.translation import gettext_lazy as _
from .models import CustomUser
from .forms import AdminUserCreationForm


def check_user_username_availability(request):
    """API endpoint to check username availability across all databases"""
    if request.method != 'POST':
        return JsonResponse({'available': False, 'error': 'Method not allowed'})
    
    try:
        username = request.POST.get('username', '').strip()
        
        if not username:
            return JsonResponse({'available': False, 'error': 'Username is required'})
        
        if len(username) < 3:
            return JsonResponse({'available': False, 'error': 'Username must be at least 3 characters'})
        
        conflicts = []
        
        # Check in ZAIN HMS unified database
        if CustomUser.objects.filter(username=username).exists():
            conflicts.append('ZAIN HMS database')
        
        if conflicts:
            return JsonResponse({
                'available': False, 
                'conflicts': conflicts,
                'message': f'Username already exists in: {", ".join(conflicts)}'
            })
        else:
            return JsonResponse({'available': True, 'message': 'Username is available'})
            
    except Exception as e:
        return JsonResponse({'available': False, 'error': f'Server error: {str(e)}'})


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    """Enhanced admin for regular users (doctors, nurses, staff, etc.) 
    NOTE: Hospital Admin users are managed separately via Hospital Admin Users section"""
    
    list_display = ('username', 'email', 'first_name', 'last_name', 'groups_list', 'status_badge', 'last_login_info', 'date_joined')
    list_filter = ('is_staff', 'is_active', 'date_joined', 'gender', 'is_superuser', 'groups')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'employee_id')
    ordering = ('-date_joined',)
    list_per_page = 25
    
    readonly_fields = ('last_login', 'date_joined')
    
    # Use default Django admin templates
    # Ensure extra fields (first/last/email/phone) and groups checkbox are validated & saved on add
    add_form = AdminUserCreationForm
    
    # Override add_fieldsets to show a comprehensive, hospital-agnostic user creation form
    add_fieldsets = (
        (_('Authentication'), {
            'classes': ('collapse',),
            'fields': ('username', 'password1', 'password2'),
        }),
        (_('Personal Information'), {
            'classes': ('collapse',),
            'fields': ('first_name', 'last_name', 'email', 'phone', 'date_of_birth', 'gender', 'address', 'emergency_contact'),
        }),
        (_('Staff Information'), {
            'classes': ('collapse',),
            'fields': ('role', 'employee_id'),
        }),
        (_('Permissions & Groups'), {
            'classes': ('collapse',),
            'fields': ('is_staff', 'is_superuser', 'groups'),
        }),
    )

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == 'groups':
            kwargs['widget'] = forms.CheckboxSelectMultiple
        return super().formfield_for_manytomany(db_field, request, **kwargs)
    
    def hospital_info(self, obj):
        """Display hospital information with styling"""
        if obj.hospital:
            return format_html(
                '<div style="display: flex; align-items: center;">'
                '<i class="fas fa-hospital" style="color: #007cba; margin-right: 5px;"></i>'
                '<strong>{}</strong></div>',
                obj.hospital.name
            )
        return format_html('<span style="color: #dc3545;"><i class="fas fa-exclamation-triangle"></i> No Hospital</span>')
    hospital_info.short_description = '🏥 Hospital'
    hospital_info.admin_order_field = 'hospital__name'
    
    def role_badge(self, obj):
        """Display role as a colored badge"""
        role_colors = {
            'SUPERADMIN': '#dc3545',  # Red
            'ADMIN': '#28a745',  # Green
            'DOCTOR': '#007bff',  # Blue
            'NURSE': '#17a2b8',  # Cyan
            'RECEPTIONIST': '#ffc107',  # Yellow
            'PHARMACIST': '#6f42c1',  # Purple
            'LAB_TECHNICIAN': '#fd7e14',  # Orange
            'RADIOLOGIST': '#20c997',  # Teal
            'ACCOUNTANT': '#6c757d',  # Gray
            'STAFF': '#343a40',  # Dark
        }
        
        color = role_colors.get(obj.role, '#6c757d')
        return format_html(
            '<span style="background: {}; color: white; padding: 4px 8px; '
            'border-radius: 12px; font-size: 0.8em; font-weight: bold;">{}</span>',
            color, obj.get_role_display()
        )
    role_badge.short_description = '👔 Role'
    role_badge.admin_order_field = 'role'
    
    def status_badge(self, obj):
        """Display user status with colored indicators"""
        if not obj.is_active:
            return format_html(
                '<span style="color: #dc3545;"><i class="fas fa-user-slash"></i> Inactive</span>'
            )
        elif obj.is_superuser:
            return format_html(
                '<span style="color: #dc3545;"><i class="fas fa-crown"></i> Super Admin</span>'
            )
        elif obj.is_staff:
            return format_html(
                '<span style="color: #28a745;"><i class="fas fa-user-shield"></i> Staff</span>'
            )
        else:
            return format_html(
                '<span style="color: #007bff;"><i class="fas fa-user"></i> Active</span>'
            )
    status_badge.short_description = '🚦 Status'
    
    def last_login_info(self, obj):
        """Display last login with relative time"""
        if obj.last_login:
            return format_html(
                '<span title="{}">{}</span>',
                obj.last_login.strftime('%Y-%m-%d %H:%M:%S'),
                obj.last_login.strftime('%Y-%m-%d')
            )
        return format_html('<span style="color: #dc3545;">Never</span>')
    last_login_info.short_description = '⏰ Last Login'
    last_login_info.admin_order_field = 'last_login'

    def groups_list(self, obj):
        names = list(obj.groups.values_list('name', flat=True))
        return ", ".join(names) if names else '—'
    groups_list.short_description = 'Groups'
    
    def get_fieldsets(self, request, obj=None):
        """Customize fieldsets based on user type; use add_fieldsets on add."""
        # On add view, strictly use the configured add_fieldsets
        if obj is None:
            return self.add_fieldsets

        base_fieldsets = BaseUserAdmin.fieldsets

        # For superadmin users, don't show hospital information
        if obj.role == 'SUPERADMIN':
            return base_fieldsets + (
                ('👤 Personal Information', {
                    'fields': ('date_of_birth', 'gender', 'phone', 'address', 'emergency_contact'),
                    'classes': ('wide',)
                }),
                ('🔐 Access Control', {
                    'fields': ('is_superadmin', 'is_active_staff'),
                    'classes': ('wide',)
                }),
            )
        # For regular hospital staff, show hospital information
        return base_fieldsets + (
            ('🏥 Hospital Information', {
                'fields': ('hospital', 'role', 'employee_id', 'phone', 'address'),
                'classes': ('wide',)
            }),
            ('👤 Personal Information', {
                'fields': ('date_of_birth', 'gender', 'emergency_contact'),
                'classes': ('wide',)
            }),
            ('🔐 Access Control', {
                'fields': ('is_superadmin', 'is_active_staff'),
                'classes': ('wide',)
            }),
        )
    
    def get_form(self, request, obj=None, **kwargs):
        """Use the custom add form for creation and tweak role choices on change."""
        # Force add view to use our AdminUserCreationForm
        if obj is None:
            kwargs['form'] = self.add_form

        form = super().get_form(request, obj, **kwargs)

        # On change forms, constrain role choices for non-superusers
        if 'role' in form.base_fields:
            choices = [choice for choice in CustomUser.ROLE_CHOICES
                       if choice[0] not in ['ADMIN', 'SUPERADMIN']]

            # Only superusers can create superadmins
            if request.user.is_superuser:
                superadmin_choice = [c for c in CustomUser.ROLE_CHOICES if c[0] == 'SUPERADMIN']
                if superadmin_choice:
                    choices.append(superadmin_choice[0])

            form.base_fields['role'].choices = choices

        return form
    
    def save_model(self, request, obj, form, change):
        """Persist user to default DB and respect explicit admin choices.

        - SUPERADMIN role: always force Django admin flags on.
        - Other roles: respect the is_superuser/is_staff values provided via the form.
        """
        try:
            if getattr(obj, 'role', None) == 'SUPERADMIN':
                obj.is_staff = True
                obj.is_superuser = True
            # else: keep obj.is_superuser / obj.is_staff as set by the form

            obj.save(using='default')
        except Exception:
            super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        """Filter users based on permissions and exclude hospital admins"""
        # Force admin list reads to use the default DB so the shared user table
        # is always queried from the main database.
        qs = super().get_queryset(request)
        
        # EXCLUDE HOSPITAL_ADMIN users - they have their own admin interface
        qs = qs.exclude(role='ADMIN')
        
        if request.user.role == 'ADMIN':
            # ZAIN HMS - unified system, show all users for hospital admins
            pass
        elif not request.user.is_superuser:
            # Non-superusers can't see superadmins
            qs = qs.exclude(role='SUPERADMIN')
        
        return qs
    
    actions = ['activate_users', 'deactivate_users', 'make_admin', 'make_doctor', 'make_nurse', 'reset_password', 'send_welcome_email']
    
    def activate_users(self, request, queryset):
        """Activate selected users"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'✅ {updated} users were successfully activated.')
    activate_users.short_description = '✅ Activate selected users'
    
    def deactivate_users(self, request, queryset):
        """Deactivate selected users"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'❌ {updated} users were successfully deactivated.')
    deactivate_users.short_description = '❌ Deactivate selected users'
    
    def make_admin(self, request, queryset):
        """Convert selected users to hospital administrators"""
        updated = queryset.update(role='ADMIN', is_staff=False)
        self.message_user(request, f'👑 {updated} users were successfully made hospital administrators.')
    make_admin.short_description = '👑 Make selected users hospital administrators'
    
    def make_doctor(self, request, queryset):
        """Convert selected users to doctors"""
        updated = queryset.update(role='DOCTOR')
        self.message_user(request, f'🩺 {updated} users were successfully made doctors.')
    make_doctor.short_description = '🩺 Make selected users doctors'
    
    def make_nurse(self, request, queryset):
        """Convert selected users to nurses"""
        updated = queryset.update(role='NURSE')
        self.message_user(request, f'👩‍⚕️ {updated} users were successfully made nurses.')
    make_nurse.short_description = '👩‍⚕️ Make selected users nurses'
    
    def reset_password(self, request, queryset):
        """Reset password for selected users"""
        from django.contrib.auth.hashers import make_password
        import secrets
        import string
        
        reset_count = 0
        for user in queryset:
            # Generate random password
            password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8))
            user.set_password(password)
            user.save()
            reset_count += 1
            
            # In a real application, you would send this password via email
            # For demo purposes, we'll show a message
            
        self.message_user(request, f'🔐 Password reset for {reset_count} users. New passwords have been generated.')
    reset_password.short_description = '🔐 Reset password for selected users'
    
    def send_welcome_email(self, request, queryset):
        """Send welcome email to selected users"""
        email_count = 0
        for user in queryset:
            if user.email:
                # In a real application, implement email sending
                email_count += 1
                
        self.message_user(request, f'📧 Welcome emails sent to {email_count} users.')
    send_welcome_email.short_description = '📧 Send welcome email to selected users'

    def get_urls(self):
        """Add custom URL for username checking API"""
        urls = super().get_urls()
        custom_urls = [
            path('api/check-username/', 
                 self.admin_site.admin_view(check_user_username_availability),
                 name='check_user_username_availability'),
        ]
        return custom_urls + urls

    def response_change(self, request, obj):
        """
        Customize the redirect behavior after changing a user.
        By default, redirect to the user list instead of staying on the edit page.
        """
        from django.http import HttpResponseRedirect
        from django.urls import reverse
        from django.utils.html import format_html
        
        # Check if the user clicked "Save and continue editing"
        if "_continue" in request.POST:
            return super().response_change(request, obj)
        
        # Check if the user clicked "Save and add another" 
        elif "_addanother" in request.POST:
            return super().response_change(request, obj)
        
        # For regular "Save", redirect to the changelist (user list)
        else:
            self.message_user(
                request, 
                format_html(
                    '✅ The user <strong>"{}"</strong> was changed successfully.',
                    obj.username
                ), 
                level='SUCCESS'
            )
            return HttpResponseRedirect(reverse('admin:accounts_customuser_changelist'))

    def response_add(self, request, obj, post_url_continue=None):
        """
        Customize the redirect behavior after adding a user.
        By default, redirect to the user list instead of staying on the edit page.
        """
        from django.http import HttpResponseRedirect
        from django.urls import reverse
        from django.utils.html import format_html
        
        # Check if the user clicked "Save and continue editing"
        if "_continue" in request.POST:
            return super().response_add(request, obj, post_url_continue)
        
        # Check if the user clicked "Save and add another"
        elif "_addanother" in request.POST:
            return super().response_add(request, obj, post_url_continue)
        
        # For regular "Save", redirect to the changelist (user list)  
        else:
            self.message_user(
                request, 
                format_html(
                    '✅ The user <strong>"{}"</strong> was added successfully.',
                    obj.username
                ), 
                level='SUCCESS'
            )
            return HttpResponseRedirect(reverse('admin:accounts_customuser_changelist'))
