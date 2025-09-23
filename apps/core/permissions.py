"""
Enterprise-Grade Permission System for ZAIN HMS
Provides role-based access control and permission decorators
"""

from functools import wraps
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
import logging

# Security logger
security_logger = logging.getLogger('zain_hms.security')


class RoleBasedPermissionMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin that provides role-based access control for class-based views
    """
    required_roles = []  # List of roles that can access this view
    required_permissions = []  # List of specific permissions required
    
    def test_func(self):
        """Test if user has required role and permissions"""
        user = self.request.user
        
        # Check if user has role attribute
        if not hasattr(user, 'role'):
            security_logger.error(f"User {user.username} has no role assigned")
            return False
        
        # Superadmin can access everything
        if user.role == 'SUPERADMIN':
            return True
        
        # Check required roles
        if self.required_roles and user.role not in self.required_roles:
            security_logger.warning(
                f"Role check failed: User {user.username} (Role: {user.role}) "
                f"tried to access view requiring roles: {self.required_roles}"
            )
            return False
        
        # Check specific permissions if defined
        if self.required_permissions:
            for permission in self.required_permissions:
                if not user.has_perm(permission):
                    security_logger.warning(
                        f"Permission check failed: User {user.username} lacks permission: {permission}"
                    )
                    return False
        
        return True
    
    def handle_no_permission(self):
        """Handle when user doesn't have permission"""
        if not self.request.user.is_authenticated:
            # Redirect unauthenticated users to login page
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(self.request.get_full_path())
        
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'error': 'Access denied - Insufficient permissions'
            }, status=403)
        
        messages.error(self.request, 'You do not have permission to access this page.')
        return HttpResponseForbidden('Access Denied - Insufficient Permissions')


class PatientAccessMixin(RoleBasedPermissionMixin):
    """Mixin for patient-related views"""
    required_roles = ['SUPERADMIN', 'HOSPITAL_ADMIN', 'DOCTOR', 'NURSE', 'STAFF', 'RECEPTIONIST']


class DoctorAccessMixin(RoleBasedPermissionMixin):
    """Mixin for doctor-only views"""
    required_roles = ['SUPERADMIN', 'HOSPITAL_ADMIN', 'DOCTOR']


class AdminAccessMixin(RoleBasedPermissionMixin):
    """Mixin for admin-only views"""
    required_roles = ['SUPERADMIN', 'HOSPITAL_ADMIN']


class StaffAccessMixin(RoleBasedPermissionMixin):
    """Mixin for staff-level access"""
    required_roles = ['SUPERADMIN', 'HOSPITAL_ADMIN', 'DOCTOR', 'NURSE', 'STAFF']


class ReportsAccessMixin(RoleBasedPermissionMixin):
    """Mixin for reports access"""
    required_roles = ['SUPERADMIN', 'HOSPITAL_ADMIN', 'DOCTOR', 'NURSE']


class BillingAccessMixin(RoleBasedPermissionMixin):
    """Mixin for billing access"""
    required_roles = ['SUPERADMIN', 'HOSPITAL_ADMIN', 'STAFF']


class EmergencyAccessMixin(RoleBasedPermissionMixin):
    """Mixin for emergency department access"""
    required_roles = ['SUPERADMIN', 'HOSPITAL_ADMIN', 'DOCTOR', 'NURSE']


class PharmacyAccessMixin(RoleBasedPermissionMixin):
    """Mixin for pharmacy access"""
    required_roles = ['SUPERADMIN', 'HOSPITAL_ADMIN', 'DOCTOR', 'NURSE', 'PHARMACIST']


class LaboratoryAccessMixin(RoleBasedPermissionMixin):
    """Mixin for laboratory access"""
    required_roles = ['SUPERADMIN', 'HOSPITAL_ADMIN', 'DOCTOR', 'NURSE', 'LAB_TECHNICIAN']


# Decorator functions for function-based views

def role_required(*roles):
    """
    Decorator that requires user to have one of the specified roles
    Usage: @role_required('DOCTOR', 'NURSE')
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            user = request.user
            
            # Check if user has role attribute
            if not hasattr(user, 'role'):
                security_logger.error(f"User {user.username} has no role assigned")
                messages.error(request, 'Your account is not properly configured. Please contact administrator.')
                return redirect('core:home')
            
            # Superadmin can access everything
            if user.role == 'SUPERADMIN':
                return view_func(request, *args, **kwargs)
            
            # Check if user has required role
            if user.role not in roles:
                security_logger.warning(
                    f"Role check failed: User {user.username} (Role: {user.role}) "
                    f"tried to access view requiring roles: {roles}"
                )
                
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({
                        'error': 'Access denied - Insufficient permissions'
                    }, status=403)
                
                messages.error(request, 'You do not have permission to access this page.')
                return HttpResponseForbidden('Access Denied - Insufficient Permissions')
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def patient_access_required(view_func):
    """Decorator for patient-related views"""
    return role_required('SUPERADMIN', 'HOSPITAL_ADMIN', 'DOCTOR', 'NURSE', 'STAFF', 'RECEPTIONIST')(view_func)


def doctor_access_required(view_func):
    """Decorator for doctor-only views"""
    return role_required('SUPERADMIN', 'HOSPITAL_ADMIN', 'DOCTOR')(view_func)


def admin_access_required(view_func):
    """Decorator for admin-only views"""
    return role_required('SUPERADMIN', 'HOSPITAL_ADMIN')(view_func)


def staff_access_required(view_func):
    """Decorator for staff-level access"""
    return role_required('SUPERADMIN', 'HOSPITAL_ADMIN', 'DOCTOR', 'NURSE', 'STAFF')(view_func)


def reports_access_required(view_func):
    """Decorator for reports access"""
    return role_required('SUPERADMIN', 'HOSPITAL_ADMIN', 'DOCTOR', 'NURSE')(view_func)


def billing_access_required(view_func):
    """Decorator for billing access"""
    return role_required('SUPERADMIN', 'HOSPITAL_ADMIN', 'STAFF')(view_func)


def emergency_access_required(view_func):
    """Decorator for emergency access"""
    return role_required('SUPERADMIN', 'HOSPITAL_ADMIN', 'DOCTOR', 'NURSE')(view_func)


def audit_action(action_type):
    """
    Decorator to audit user actions
    Usage: @audit_action('PATIENT_CREATE')
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Execute the view
            response = view_func(request, *args, **kwargs)
            
            # Log the action
            security_logger.info(
                f"AUDIT: User {request.user.username} performed action {action_type} "
                f"from IP {get_client_ip(request)} at {request.path}"
            )
            
            return response
        return _wrapped_view
    return decorator


def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR', 'unknown')
    return ip


class SecureViewMixin(RoleBasedPermissionMixin):
    """
    Comprehensive secure view mixin that combines:
    - Authentication requirement
    - Role-based access control
    - Audit logging
    """
    
    def dispatch(self, request, *args, **kwargs):
        # Log the access attempt
        security_logger.info(
            f"SECURE_VIEW_ACCESS: User {request.user.username if request.user.is_authenticated else 'anonymous'} "
            f"accessing {self.__class__.__name__} from IP {get_client_ip(request)}"
        )
        
        return super().dispatch(request, *args, **kwargs)
