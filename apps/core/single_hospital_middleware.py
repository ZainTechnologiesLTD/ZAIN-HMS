# apps/core/single_hospital_middleware.py
from django.shortcuts import redirect
from django.urls import reverse, resolve
from django.contrib.auth.views import LoginView
from apps.tenants.models import Tenant

class SingleHospitalMiddleware:
    """
    Simplified middleware for single hospital per user approach.
    Each user belongs to exactly one hospital - no selection needed.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Paths that don't require hospital context
        self.exempt_paths = [
            '/admin/',
            '/accounts/login/',
            '/accounts/logout/',
            '/accounts/password/',
            '/static/',
            '/media/',
        ]

    def __call__(self, request):
        # Skip middleware for exempt paths
        if any(request.path.startswith(path) for path in self.exempt_paths):
            return self.get_response(request)
            
        # Skip for unauthenticated users
        if not request.user.is_authenticated:
            return self.get_response(request)
            
        # Handle superadmin users - they can access any hospital via URL parameter
        if request.user.is_superuser or request.user.role == 'SUPERADMIN':
            self._handle_superadmin(request)
        else:
            # Regular users - automatically set their hospital context
            self._handle_regular_user(request)
        
        response = self.get_response(request)
        return response
    
    def _handle_superadmin(self, request):
        """Handle superadmin access - they can view any hospital via ?hospital_id=X"""
        hospital_id = request.GET.get('hospital_id')
        
        if hospital_id:
            try:
                hospital = Tenant.objects.get(id=hospital_id, is_active=True)
                request.hospital = hospital
                request.user_role = 'SUPERADMIN'
            except Tenant.DoesNotExist:
                # Invalid hospital ID - use first available hospital
                request.hospital = Tenant.objects.filter(is_active=True).first()
                request.user_role = 'SUPERADMIN'
        else:
            # No hospital specified - use first available hospital
            request.hospital = Tenant.objects.filter(is_active=True).first()
            request.user_role = 'SUPERADMIN'
    
    def _handle_regular_user(self, request):
        """Handle regular user - assign their hospital automatically"""
        user = request.user
        
        if user.hospital:
            # User has assigned hospital
            request.hospital = user.hospital
            request.user_role = user.role
        else:
            # User has no hospital assigned - redirect to login with error
            # This shouldn't happen in proper setup, but handle gracefully
            from django.contrib.auth import logout
            from django.contrib import messages
            
            messages.error(request, 'Your account is not assigned to any hospital. Please contact administrator.')
            logout(request)
            return redirect('accounts:login')
