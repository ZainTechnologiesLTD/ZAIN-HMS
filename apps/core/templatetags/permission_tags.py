from django import template

register = template.Library()

@register.filter
def can_access_module(user, module_name):
    """Check if user can access a module"""
    try:
        # Always allow access for superusers
        if user.is_superuser:
            return True
            
        # Check if user has role attribute
        if not hasattr(user, 'role'):
            return True  # Default to allowing access if no role system
            
        # SUPERADMIN role gets full access
        if user.role == 'SUPERADMIN':
            return True
            
        # Check if the user model has the has_module_permission method
        if hasattr(user, 'has_module_permission'):
            return user.has_module_permission(module_name)
        else:
            # Fallback: allow access for common roles
            return True
            
    except Exception as e:
        # If anything fails, default to allowing access
        # You can log the error here if needed
        return True

@register.simple_tag
def get_user_role(user):
    """Get user role safely"""
    try:
        return getattr(user, 'role', 'USER')
    except:
        return 'USER'
