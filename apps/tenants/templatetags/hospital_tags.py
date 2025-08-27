# apps/tenants/templatetags/hospital_tags.py
from django import template
from apps.tenants.models import Tenant, TenantAccess

register = template.Library()


@register.inclusion_tag('tenants/hospital_context.html', takes_context=True)
def hospital_context(context):
    """Include hospital context information for templates - Simplified for single hospital approach"""
    request = context.get('request')
    if not request:
        return {'hospital': None, 'user_role': None, 'enabled_modules': []}
        
    user = request.user
    
    if not user.is_authenticated:
        return {'hospital': None, 'user_role': None, 'enabled_modules': []}
    
    try:
        hospital = user.hospital  # Direct hospital relationship
        user_role = user.role  # Direct role from user
        
        return {
            'hospital': hospital,
            'user_role': user_role,
            'enabled_modules': hospital.get_enabled_modules() if hospital else [],
        }
    except Exception as e:
        # Return safe defaults if there are any database or method errors
        return {'hospital': None, 'user_role': None, 'enabled_modules': []}


@register.filter
def has_module_access(user, module_name):
    """Check if user has access to a specific module"""
    # Handle None user or unauthenticated users
    if not user or not hasattr(user, 'is_authenticated') or not user.is_authenticated:
        return False
    
    try:
        current_hospital = user.get_current_hospital()
        if not current_hospital:
            return False
        
        # Check if module is enabled for this hospital
        module_enabled = getattr(current_hospital, f'{module_name}_enabled', True)
        if not module_enabled:
            return False
        
        return user.has_module_permission(module_name)
    except Exception:
        return False


@register.simple_tag
def get_hospital_logo(hospital):
    """Get hospital logo URL"""
    if hospital and hospital.logo:
        return hospital.logo.url
    return '/static/images/default-hospital-logo.png'


@register.simple_tag
def get_subscription_status(hospital):
    """Get subscription status with styling"""
    if not hospital:
        return ''
    
    if hospital.is_trial:
        return f'<span class="badge badge-warning">Trial ({hospital.days_until_expiry} days left)</span>'
    elif hospital.is_subscription_active:
        return f'<span class="badge badge-success">Active ({hospital.days_until_expiry} days left)</span>'
    else:
        return '<span class="badge badge-danger">Expired</span>'
