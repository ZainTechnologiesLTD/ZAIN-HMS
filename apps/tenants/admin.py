from django.contrib import admin
from django.contrib.auth import get_user_model
from django.forms import ModelForm, ModelChoiceField
from django.db import models, transaction
from django.contrib import messages
from django.utils.html import format_html
from django.utils import timezone
from datetime import timedelta
from .models import Tenant, TenantAccess
from .utils import AllowedHostsManager

User = get_user_model()


class TenantAdminForm(ModelForm):
    """Custom form for Tenant admin"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show users who can be hospital admins
        self.fields['admin'].queryset = User.objects.filter(
            models.Q(role='HOSPITAL_ADMIN') | models.Q(role='SUPERADMIN')
        )
        self.fields['admin'].empty_label = "Select Hospital Administrator"
        
        # Set default values for required fields if this is a new instance
        if not self.instance.pk:
            # Set default subscription dates for new hospitals
            now = timezone.now()
            self.fields['subscription_start_date'].initial = now
            self.fields['subscription_end_date'].initial = now + timedelta(days=365)  # 1 year
            self.fields['trial_end_date'].initial = now + timedelta(days=30)  # 30 day trial
    
    def clean(self):
        """Auto-generate db_name if not provided"""
        cleaned_data = super().clean()
        subdomain = cleaned_data.get('subdomain')
        db_name = cleaned_data.get('db_name')
        
        # Auto-generate db_name from subdomain if not provided
        if subdomain and not db_name:
            cleaned_data['db_name'] = f"hospital_{subdomain}"
        
        return cleaned_data


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    """Admin interface for Hospital Tenants with SaaS Features"""
    form = TenantAdminForm
    list_display = ['name', 'subdomain', 'admin', 'subscription_plan', 'subscription_status', 'database_status', 'is_active', 'created_at']
    list_filter = ['subscription_plan', 'is_active', 'is_trial', 'is_suspended', 'created_at']
    search_fields = ['name', 'subdomain', 'admin__username', 'admin__first_name', 'admin__last_name']
    
    fieldsets = (
        ('Hospital Information', {
            'fields': ('name', 'subdomain', 'db_name', 'logo'),
            'description': '<div style="background: #e8f5e8; padding: 10px; border-radius: 5px; margin-bottom: 10px;">'
                          '<strong>🎉 Automatic Database Setup:</strong><br/>'
                          'When you save this hospital, a dedicated database will be automatically created with all necessary modules:<br/>'
                          '<ul style="margin: 5px 0; padding-left: 20px;">'
                          '<li><strong>Patient Management:</strong> Patient records, registration, medical history</li>'
                          '<li><strong>Appointment System:</strong> Scheduling, calendar, notifications</li>'  
                          '<li><strong>Staff Management:</strong> Doctors, nurses, staff profiles</li>'
                          '<li><strong>Medical Modules:</strong> Laboratory, surgery, emergency, IPD/OPD</li>'
                          '<li><strong>Business Modules:</strong> Billing, inventory, analytics, reports</li>'
                          '<li><strong>Communication:</strong> Notifications, telemedicine, feedback</li>'
                          '</ul>'
                          'Database will be created as: <code>hospital_{subdomain}</code><br/>'
                          'You will see a confirmation message after successful creation.'
                          '</div>'
        }),
        ('Administrator', {
            'fields': ('admin',),
            'description': 'Select a user with Hospital Administrator role'
        }),
        ('Contact Information', {
            'fields': ('address', 'phone', 'email', 'website'),
        }),
        ('Subscription & Billing', {
            'fields': ('subscription_plan', 'subscription_start_date', 'subscription_end_date', 'trial_end_date', 'is_trial'),
            'classes': ('wide',)
        }),
        ('Limits & Quotas', {
            'fields': ('max_users', 'max_patients', 'max_storage_gb'),
            'classes': ('collapse',)
        }),
        ('Module Access', {
            'fields': ('telemedicine_enabled', 'laboratory_enabled', 'radiology_enabled', 'pharmacy_enabled', 
                      'billing_enabled', 'ipd_enabled', 'emergency_enabled'),
            'classes': ('wide',),
            'description': 'Enable/disable modules based on subscription plan'
        }),
        ('Status', {
            'fields': ('is_active', 'is_suspended')
        }),
    )
    
    def subscription_status(self, obj):
        """Display subscription status with color coding"""
        if obj.is_trial:
            return format_html('<span style="color: orange;">Trial</span>')
        elif obj.is_subscription_active:
            return format_html('<span style="color: green;">Active</span>')
        else:
            return format_html('<span style="color: red;">Expired</span>')
    subscription_status.short_description = 'Status'
    
    def database_status(self, obj):
        """Display database status with color coding"""
        try:
            from django.conf import settings
            from django.db import connections
            
            db_name = f"hospital_{obj.subdomain}"
            
            if db_name in settings.DATABASES:
                try:
                    connection = connections[db_name]
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                        tables = cursor.fetchall()
                        table_count = len(tables)
                    
                    if table_count > 10:  # Reasonable number of tables for a functional hospital DB
                        return format_html(
                            '<span style="color: green;" title="{} tables">✅ Ready</span>', 
                            table_count
                        )
                    else:
                        return format_html(
                            '<span style="color: orange;" title="{} tables">⚠️ Incomplete</span>', 
                            table_count
                        )
                except:
                    return format_html('<span style="color: red;" title="Connection failed">❌ Error</span>')
            else:
                return format_html('<span style="color: red;" title="Not configured">❌ Missing</span>')
                
        except Exception as e:
            return format_html('<span style="color: gray;" title="{}">❓ Unknown</span>', str(e))
    
    database_status.short_description = 'Database'
    
    def save_model(self, request, obj, form, change):
        """Create TenantAccess and hospital database when hospital is created/updated"""
        is_new = not change
        
        # Validate required fields before saving
        if not obj.admin_id:
            messages.error(request, "❌ Hospital Administrator is required.")
            return
        
        # Save the tenant explicitly to the default database to avoid accidental
        # routing to a tenant-specific DB (which causes FOREIGN KEY failures
        # when creating related TenantAccess records in the shared DB).
        try:
            # Use form.save(commit=False) to get the instance and save using 'default'
            saved_obj = form.save(commit=False)
            saved_obj.save(using='default')
            # Save any m2m relationships (will use default DB connections)
            try:
                form.save_m2m()
            except Exception:
                # If form has no m2m or save_m2m fails, ignore but continue
                pass
            # Refresh obj to ensure it's the instance from default DB
            obj = Tenant.objects.using('default').get(pk=saved_obj.pk)
        except Exception:
            # Fallback to default ModelAdmin save if something unexpected happens
            super().save_model(request, obj, form, change)
        
        # Auto-create database and configure ALLOWED_HOSTS for new hospitals
        if is_new:
            try:
                from apps.core.db_router import TenantDatabaseManager
                hospital_code = obj.subdomain
                
                # Add hospital subdomain to ALLOWED_HOSTS
                AllowedHostsManager.add_hospital_domain(hospital_code)
                
                # Create the hospital database with all necessary modules
                TenantDatabaseManager.create_hospital_database(hospital_code)
                
                # Get list of migrated modules for display
                migrated_modules = [
                    'Patient Management', 'Appointments', 'Doctors & Staff', 'Nurses',
                    'Billing & Invoicing', 'Laboratory', 'Emergency Care', 'Inventory',
                    'Analytics & Reports', 'Human Resources', 'Surgery Management',
                    'Telemedicine', 'Room Management', 'OPD/IPD', 'Notifications',
                    'Contact Management', 'Feedback System', 'Dashboard'
                ]
                
                # Get hospital URL
                hospital_url = AllowedHostsManager.get_hospital_url(hospital_code)
                
                # Display success message
                messages.success(
                    request, 
                    format_html(
                        '<div style="background: #d4edda; border: 1px solid #c3e6cb; padding: 15px; border-radius: 8px;">'
                        '<h4 style="color: #155724; margin: 0 0 10px 0;">🎉 Hospital Created Successfully!</h4>'
                        '<p><strong>Hospital:</strong> {}</p>'
                        '<p><strong>Database:</strong> hospital_{}</p>'
                        '<p><strong>Domain:</strong> {}.localhost (added to ALLOWED_HOSTS)</p>'
                        '<p><strong>Modules Migrated:</strong></p>'
                        '<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 5px; margin: 10px 0;">'
                        '{}'
                        '</div>'
                        '<p style="margin-top: 15px;">'
                        '<a href="{}" target="_blank" '
                        'style="background: #28a745; color: white; padding: 8px 16px; text-decoration: none; border-radius: 4px;">'
                        '🚀 Access Hospital Dashboard</a>'
                        '</p>'
                        '</div>',
                        obj.name, 
                        hospital_code,
                        hospital_code,
                        ''.join([f'<span style="background: #f8f9fa; padding: 2px 6px; border-radius: 3px; font-size: 12px;">✅ {module}</span>' 
                                for module in migrated_modules]),
                        hospital_url
                    )
                )
                
                # Create TenantAccess and set user.hospital after transaction is committed
                def create_admin_access():
                    import logging, traceback
                    logger = logging.getLogger(__name__)
                    if obj.admin:
                        try:
                            # Verify the selected admin user exists in the shared/default DB
                            user_in_default = User.objects.using('default').filter(pk=obj.admin.pk).first()
                            if not user_in_default:
                                # Attempt quick diagnostic: check other hospital DBs for the user
                                from django.conf import settings as dj_settings
                                found_in = []
                                for db_key in list(dj_settings.DATABASES.keys()):
                                    if db_key.startswith('hospital_'):
                                        try:
                                            u = User.objects.using(db_key).filter(username=obj.admin.username).first()
                                            if u:
                                                found_in.append(db_key)
                                        except Exception:
                                            continue

                                msg = (
                                    f"Selected admin user '{obj.admin.username}' was not found in the main (default) database. "
                                    "This commonly happens when the user was created while a hospital DB context was active (user was saved into a tenant DB). "
                                    "Please create or move the user into the main database and try again."
                                )
                                # Log diagnostics
                                logger.error(f"Admin user missing in default DB for tenant {obj.subdomain}. Found in: {found_in}")
                                # Give admin a visible message
                                try:
                                    messages.error(request, format_html('<strong>❌ Failed to create admin access:</strong> {}<br><em>Found in:</em> {}', msg, ', '.join(found_in) or 'None'))
                                except Exception:
                                    # messages may not be available depending on transaction timing; fallback to print
                                    print('❌', msg, 'Found in:', found_in)
                                return

                            # Ensure operations happen on the shared/default database to avoid cross-db FK issues
                            TenantAccess.objects.using('default').update_or_create(
                                user=user_in_default,
                                tenant=obj,
                                defaults={
                                    'role': 'HOSPITAL_ADMIN',
                                    'is_active': True
                                }
                            )

                            # Set user's hospital field for direct authentication and save to default DB
                            User.objects.using('default').filter(pk=user_in_default.pk).update(hospital=obj)

                            logger.info(f"✅ Created admin access and set hospital for {user_in_default.username} to {obj.name}")
                        except Exception as access_error:
                            # Log full traceback for debugging cross-database FK problems
                            tb = traceback.format_exc()
                            logger.error(f"❌ Failed to create admin access for tenant {obj}: {access_error}\n{tb}")
                            # Also print to stdout to keep existing admin UI visibility
                            print(f"❌ Failed to create admin access: {access_error}")
                
                transaction.on_commit(create_admin_access)
                
            except Exception as e:
                messages.error(
                    request,
                    format_html(
                        '<div style="background: #f8d7da; border: 1px solid #f5c6cb; padding: 15px; border-radius: 8px;">'
                        '<h4 style="color: #721c24; margin: 0 0 10px 0;">⚠️ Database Creation Failed</h4>'
                        '<p><strong>Hospital:</strong> {}</p>'
                        '<p><strong>Error:</strong> {}</p>'
                        '<p><strong>What to do:</strong></p>'
                        '<ul>'
                        '<li>Check that the hospital subdomain is unique and valid</li>'
                        '<li>Ensure the database directory has write permissions</li>'
                        '<li>Try using the "Create Database" action from the hospital list</li>'
                        '<li>Contact system administrator if the problem persists</li>'
                        '</ul>'
                        '<p style="margin-top: 10px; font-style: italic; color: #6c757d;">'
                        'The hospital record was saved successfully, but the database creation failed. '
                        'You can retry database creation using the admin actions.'
                        '</p>'
                        '</div>',
                        obj.name, str(e)
                    )
                )
        
        # For existing hospitals, just update TenantAccess
        else:
            def update_admin_access():
                import logging, traceback
                logger = logging.getLogger(__name__)
                if obj.admin:
                    try:
                        # Verify admin exists in default DB
                        user_in_default = User.objects.using('default').filter(pk=obj.admin.pk).first()
                        if not user_in_default:
                            # Diagnostics: search other DBs
                            from django.conf import settings as dj_settings
                            found_in = []
                            for db_key in list(dj_settings.DATABASES.keys()):
                                if db_key.startswith('hospital_'):
                                    try:
                                        u = User.objects.using(db_key).filter(username=obj.admin.username).first()
                                        if u:
                                            found_in.append(db_key)
                                    except Exception:
                                        continue
                            msg = (
                                f"Selected admin user '{obj.admin.username}' not found in default DB. Found in: {found_in if found_in else 'None'}. "
                                "Please recreate the user in the main database and retry."
                            )
                            try:
                                messages.error(request, format_html('<strong>❌ Failed to update admin access:</strong> {}', msg))
                            except Exception:
                                print('❌', msg)
                            logger.error(msg)
                            return

                        # Update TenantAccess record on default DB
                        TenantAccess.objects.using('default').update_or_create(
                            user=user_in_default,
                            tenant=obj,
                            defaults={
                                'role': 'HOSPITAL_ADMIN',
                                'is_active': True
                            }
                        )

                        # Update user's hospital field and save to default DB
                        User.objects.using('default').filter(pk=user_in_default.pk).update(hospital=obj)

                        logger.info(f"✅ Updated admin access and hospital for {user_in_default.username} to {obj.name}")
                    except Exception as access_error:
                        tb = traceback.format_exc()
                        logger.error(f"❌ Failed to update admin access for tenant {obj}: {access_error}\n{tb}")
                        print(f"❌ Failed to update admin access: {access_error}")
            
            transaction.on_commit(update_admin_access)
    
    def delete_model(self, request, obj):
        """Remove hospital domain from ALLOWED_HOSTS when deleting hospital"""
        hospital_code = obj.subdomain
        
        # Remove hospital domain from ALLOWED_HOSTS
        AllowedHostsManager.remove_hospital_domain(hospital_code)
        
        # Delete the hospital record
        super().delete_model(request, obj)
        
        # Show success message
        messages.success(
            request,
            format_html(
                '<div style="background: #d1ecf1; border: 1px solid #bee5eb; padding: 15px; border-radius: 8px;">'
                '<h4 style="color: #0c5460; margin: 0 0 10px 0;">🗑️ Hospital Deleted Successfully</h4>'
                '<p><strong>Hospital:</strong> {}</p>'
                '<p><strong>Domain Removed:</strong> {}.localhost (removed from ALLOWED_HOSTS)</p>'
                '<p><strong>Database:</strong> hospital_{} (still exists - manual cleanup required)</p>'
                '<p style="margin-top: 10px; font-style: italic; color: #6c757d;">'
                'Note: The hospital database files still exist and can be manually removed if needed.'
                '</p>'
                '</div>',
                obj.name,
                hospital_code,
                hospital_code
            )
        )
        
    def delete_queryset(self, request, queryset):
        """Handle bulk deletion of hospitals"""
        hospital_names = []
        hospital_domains = []
        
        for hospital in queryset:
            hospital_names.append(hospital.name)
            hospital_domains.append(f"{hospital.subdomain}.localhost")
            
            # Remove from ALLOWED_HOSTS
            AllowedHostsManager.remove_hospital_domain(hospital.subdomain)
        
        # Delete the hospitals
        count = queryset.count()
        super().delete_queryset(request, queryset)
        
        # Show success message
        messages.success(
            request,
            format_html(
                '<div style="background: #d1ecf1; border: 1px solid #bee5eb; padding: 15px; border-radius: 8px;">'
                '<h4 style="color: #0c5460; margin: 0 0 10px 0;">🗑️ {count} Hospital(s) Deleted Successfully</h4>'
                '<p><strong>Hospitals:</strong> {hospitals}</p>'
                '<p><strong>Domains Removed:</strong> {domains}</p>'
                '<p style="margin-top: 10px; font-style: italic; color: #6c757d;">'
                'Note: Database files still exist and may need manual cleanup.'
                '</p>'
                '</div>',
                count=count,
                hospitals=', '.join(hospital_names),
                domains=', '.join(hospital_domains)
            )
        )

    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete hospitals"""
        return request.user.is_superuser
    
    # Custom admin actions
    actions = ['create_database', 'verify_database', 'recreate_database']
    
    def create_database(self, request, queryset):
        """Create database for selected hospitals"""
        success_count = 0
        error_count = 0
        
        for hospital in queryset:
            try:
                from apps.core.db_router import TenantDatabaseManager
                hospital_code = hospital.subdomain
                
                # Create the hospital database
                TenantDatabaseManager.create_hospital_database(hospital_code)
                success_count += 1
                
                messages.success(
                    request, 
                    f'✅ Database created for "{hospital.name}" (hospital_{hospital_code})'
                )
                
            except Exception as e:
                error_count += 1
                messages.error(
                    request, 
                    f'❌ Failed to create database for "{hospital.name}": {str(e)}'
                )
        
        if success_count > 0:
            messages.success(request, f'Successfully created {success_count} hospital database(s)')
        if error_count > 0:
            messages.warning(request, f'Failed to create {error_count} hospital database(s)')
            
    create_database.short_description = "🏗️ Create hospital database with all modules"
    
    def verify_database(self, request, queryset):
        """Verify database exists for selected hospitals"""
        for hospital in queryset:
            try:
                from django.conf import settings
                from django.db import connections
                
                db_name = f"hospital_{hospital.subdomain}"
                
                if db_name in settings.DATABASES:
                    # Try to connect to database
                    connection = connections[db_name]
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                        tables = cursor.fetchall()
                        table_count = len(tables)
                    
                    messages.success(
                        request,
                        f'✅ "{hospital.name}" database exists with {table_count} tables'
                    )
                else:
                    messages.warning(
                        request,
                        f'⚠️ "{hospital.name}" database not found in settings'
                    )
                    
            except Exception as e:
                messages.error(
                    request,
                    f'❌ Error verifying "{hospital.name}" database: {str(e)}'
                )
                
    verify_database.short_description = "🔍 Verify hospital database status"
    
    def recreate_database(self, request, queryset):
        """Recreate database for selected hospitals (WARNING: This will delete existing data)"""
        if not request.user.is_superuser:
            messages.error(request, "Only superusers can recreate databases")
            return
            
        for hospital in queryset:
            try:
                from apps.core.db_router import TenantDatabaseManager
                hospital_code = hospital.subdomain
                
                # Delete existing database (if it exists)
                try:
                    TenantDatabaseManager.delete_hospital_database(hospital_code)
                except:
                    pass  # Database might not exist
                
                # Create new database
                TenantDatabaseManager.create_hospital_database(hospital_code)
                
                messages.success(
                    request,
                    f'✅ Database recreated for "{hospital.name}" (hospital_{hospital_code})'
                )
                
            except Exception as e:
                messages.error(
                    request,
                    f'❌ Failed to recreate database for "{hospital.name}": {str(e)}'
                )
                
    recreate_database.short_description = "🔄 Recreate hospital database (DANGER: Deletes data!)"


@admin.register(TenantAccess)
class TenantAccessAdmin(admin.ModelAdmin):
    """Admin interface for Hospital Access Management"""
    list_display = ['user', 'tenant', 'role', 'is_active', 'last_accessed']
    list_filter = ['role', 'is_active', 'tenant']
    search_fields = ['user__username', 'user__email', 'tenant__name']
    
    fieldsets = (
        ('Access Information', {
            'fields': ('user', 'tenant', 'role')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'last_accessed'),
            'classes': ('collapse',)
        }),
    )
    
    def has_delete_permission(self, request, obj=None):
        """Only superusers and hospital admins can manage access"""
        return request.user.is_superuser


# TenantAccess admin temporarily disabled due to missing tenant field
# @admin.register(TenantAccess)
# class TenantAccessAdmin(admin.ModelAdmin):
#     """Admin interface for Hospital Access Management"""
#     list_display = ['user', 'role', 'is_active', 'last_accessed']
#     list_filter = ['role', 'is_active']
#     search_fields = ['user__username', 'user__email']
#     
#     fieldsets = (
#         ('Access Information', {
#             'fields': ('user', 'role')
#         }),
#         ('Status', {
#             'fields': ('is_active',)
#         }),
#         ('Timestamps', {
#             'fields': ('created_at', 'last_accessed'),
#             'classes': ('collapse',)
#         }),
#     )
#     
#     def has_delete_permission(self, request, obj=None):
#         """Only superusers and hospital admins can manage access"""
#         return request.user.is_superuser or request.user.role == 'ADMIN'
