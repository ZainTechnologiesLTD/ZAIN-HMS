# apps/accounts/decorators.py
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied


def hospital_admin_required(view_func):
    """
    Decorator that ensures the user is a hospital admin and has a hospital selected
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Check if user is authenticated
        if not request.user.is_authenticated:
            messages.error(request, 'Please log in to access this page.')
            return redirect('accounts:login')
        
        # Check if user has hospital admin role or is superuser
        if request.user.is_superuser or request.user.role == 'SUPERADMIN':
            return view_func(request, *args, **kwargs)
        
        if request.user.role != 'HOSPITAL_ADMIN':
            messages.error(request, 'You must be a hospital administrator to access this page.')
            raise PermissionDenied
        
        # Check if user has a hospital selected
        current_hospital = request.user.get_current_hospital()
        if not current_hospital:
            messages.error(request, 'Please select a hospital first.')
            return redirect('accounts:hospital_selection')
        
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view


def module_required(module_name):
    """
    Decorator that ensures the user has access to a specific module
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Check if user is authenticated
            if not request.user.is_authenticated:
                messages.error(request, 'Please log in to access this page.')
                return redirect('accounts:login')
            
            # Check if user has access to the module
            if not request.user.has_module_permission(module_name):
                messages.error(request, f'You do not have permission to access the {module_name} module.')
                raise PermissionDenied
            
            # Check if module is enabled for current hospital
            current_hospital = request.user.get_current_hospital()
            if current_hospital:
                module_enabled = getattr(current_hospital, f'{module_name}_enabled', True)
                if not module_enabled:
                    messages.error(request, f'The {module_name} module is not enabled for your hospital.')
                    return redirect('dashboard:dashboard')
            
            return view_func(request, *args, **kwargs)
        
        return _wrapped_view
    return decorator


def hospital_selected_required(view_func):
    """
    Decorator that ensures the user has selected a hospital
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Check if user is authenticated
        if not request.user.is_authenticated:
            messages.error(request, 'Please log in to access this page.')
            return redirect('accounts:login')
        
        # Check if user has a hospital selected
        current_hospital = request.user.get_current_hospital()
        if not current_hospital:
            messages.error(request, 'Please select a hospital first.')
            return redirect('accounts:hospital_selection')
        
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view
