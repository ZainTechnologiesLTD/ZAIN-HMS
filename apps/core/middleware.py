# apps/core/middleware.py
from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth import logout
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
# from tenants.models import  # Temporarily commented Tenant as Hospital
from apps.core.models import ActivityLog
import json
import uuid


class HospitalContextMiddleware(MiddlewareMixin):
    """
    Middleware to enforce hospital selection and provide hospital context.
    Ensures multi-tenant data isolation and proper hospital context for all operations.
    """
    
    # Define which roles require hospital selection  
    HOSPITAL_ROLES = ['HOSPITAL_ADMIN', 'DOCTOR', 'NURSE', 'RECEPTIONIST', 'PHARMACIST', 
                      'LAB_TECHNICIAN', 'RADIOLOGIST', 'ACCOUNTANT', 'STAFF']
    
    # Paths that don't require hospital selection
    EXEMPT_PATHS = [
        '/auth/', '/static/', '/media/', '/admin/',
        '/tenants/hospital-selection/', '/tenants/switch-hospital/',
        '/api/auth/', '/', '/home/', '/logout/'
    ]
    
    # All module paths that require hospital selection
    PROTECTED_MODULES = [
        '/dashboard/', '/patients/', '/appointments/', '/doctors/', '/nurses/', 
        '/billing/', '/pharmacy/', '/laboratory/', '/radiology/', '/emergency/',
        '/opd/', '/ipd/', '/surgery/', '/staff/', '/inventory/', '/reports/', '/settings/',
        '/analytics/', '/notifications/', '/contact/'
    ]
    
    def process_request(self, request):
        # Skip for unauthenticated users
        if not request.user.is_authenticated:
            return None
            
        # Skip exempt paths
        if any(request.path.startswith(path) for path in self.EXEMPT_PATHS):
            return None
        
        # SuperAdmins can access everything without hospital selection
        if request.user.role == 'SUPERADMIN':
            return None
            
        # Check if user role requires hospital selection
        user_role = getattr(request.user, 'role', None)
        
        if not user_role in self.HOSPITAL_ROLES:
            return None
            
        # Check if accessing protected module
        accessing_protected_module = any(request.path.startswith(path) for path in self.PROTECTED_MODULES)
        if not accessing_protected_module:
            return None
        
        # Check if user has current hospital set
        current_hospital = request.user.get_current_hospital()
        
        # If no hospital selected, redirect to selection page
        if not current_hospital:
            messages.info(request, 
                f'Please select a hospital first to access {self._get_module_name(request.path)}.')
            return redirect('tenants:hospital_selection')
        
        # Verify user still has access to current hospital
        if not request.user.has_hospital_access(current_hospital.id):
            messages.error(request, 'Your access to the selected hospital has been revoked.')
            request.user.current_hospital = None
            request.user.save()
            return redirect('tenants:hospital_selection')
            
        # Add hospital context to request for views
        request.current_hospital = current_hospital
        request.user_role_in_hospital = request.user.get_role_in_hospital(current_hospital)
        
        # Set hospital context information
        request.hospital_info = {
            'id': current_hospital.id,
            'name': current_hospital.name,
            'subdomain': current_hospital.subdomain,
            'logo': current_hospital.logo.url if current_hospital.logo else None,
            'settings': {},
        }
            
        return None
    
    def _get_module_name(self, path):
        """Extract user-friendly module name from path"""
        module_names = {
            '/dashboard/': 'Dashboard',
            '/patients/': 'Patient Management',
            '/appointments/': 'Appointments',
            '/doctors/': 'Doctor Management',
            '/nurses/': 'Nurse Management',
            '/billing/': 'Billing',
            '/pharmacy/': 'Pharmacy',
            '/laboratory/': 'Laboratory',
            '/radiology/': 'Radiology',
            '/emergency/': 'Emergency',
            '/opd/': 'OPD',
            '/ipd/': 'IPD',
            '/surgery/': 'Surgery',
            '/staff/': 'Staff Management',
            '/inventory/': 'Inventory',
            '/reports/': 'Reports',
            '/analytics/': 'Analytics',
            '/notifications/': 'Notifications',
        }
        for prefix, name in module_names.items():
            if path.startswith(prefix):
                return name
        return 'the requested page'


class HospitalMiddleware(MiddlewareMixin):
    """Enhanced multi-tenant middleware to handle hospital-specific requests"""
    
    def process_request(self, request):
        # Skip for admin and API endpoints
        if request.path.startswith('/admin/') or request.path.startswith('/api/'):
            return None

        # Skip for unauthenticated users on certain paths
        public_paths = ['/auth/login/', '/auth/register/', '/auth/password-reset/', '/static/', '/media/']
        if not request.user.is_authenticated and any(request.path.startswith(path) for path in public_paths):
            return None

        # Skip for unauthenticated users
        if not request.user.is_authenticated:
            return None

        # Super admin can access all hospitals (role SUPERADMIN or Django is_superuser)
        if getattr(request.user, 'role', '') == 'SUPERADMIN' or request.user.is_superuser:
            # Allow hospital selection pages
            if any(p in request.path for p in ['/hospital-selection/', '/select-hospital/', '/clear-hospital-selection/', '/multi-hospital-selection/']):
                return None

            # Use hospital from query or session if provided; otherwise require selection for protected modules
            hospital_id = request.GET.get('hospital_id') or request.session.get('selected_hospital_id')
            if hospital_id:
                # Persist session markers; avoid DB lookups
                request.session['selected_hospital_id'] = str(hospital_id)
                request.session.setdefault('selected_hospital_name', 'Selected Hospital')
                request.hospital_info = {
                    'name': request.session.get('selected_hospital_name', 'Selected Hospital'),
                    'code': request.session.get('selected_hospital_code'),
                    'logo': None,
                    'settings': {},
                }
            else:
                protected_paths = ['/dashboard/', '/patients/', '/appointments/', '/doctors/', '/nurses/', '/billing/', '/pharmacy/', '/laboratory/', '/radiology/']
                if any(request.path.startswith(path) for path in protected_paths):
                    messages.info(request, 'Select a hospital to continue to the dashboard.')
                    return redirect('tenants:hospital_selection')
            return None

        # Handle multi-hospital users (doctors, nurses, etc.)
        if hasattr(request.user, 'hospital_affiliations') and request.user.hospital_affiliations.filter(is_active=True).count() > 1:
            if any(p in request.path for p in ['/multi-hospital-selection/', '/select-working-hospital/']):
                return None

            hospital_id = request.GET.get('hospital_id') or request.session.get('selected_hospital_id')
            if hospital_id:
                # Minimal session persistence; optionally add access checks in your accounts app
                request.session['selected_hospital_id'] = str(hospital_id)
                request.session.setdefault('selected_hospital_name', 'Selected Hospital')
                request.hospital_info = {
                    'name': request.session.get('selected_hospital_name', 'Selected Hospital'),
                    'code': request.session.get('selected_hospital_code'),
                    'logo': None,
                    'settings': {},
                }
            else:
                # Require explicit selection before accessing protected modules
                protected_paths = ['/dashboard/', '/patients/', '/appointments/', '/doctors/', '/nurses/', '/billing/', '/pharmacy/', '/laboratory/', '/radiology/']
                if any(request.path.startswith(path) for path in protected_paths):
                    messages.info(request, 'Select your working hospital to continue.')
                    return redirect('tenants:hospital_selection')
            return None

        # Default: user must have a hospital assigned
        if getattr(request.user, 'hospital_id', None):
            request.hospital = request.user.hospital
            request.hospital_info = {
                'name': request.user.hospital.name,
                'code': request.user.hospital.code,
                'logo': request.user.hospital.logo.url if request.user.hospital.logo else None,
                'settings': request.user.hospital.settings,
            }
            return None
        else:
            logout(request)
            messages.error(request, 'Your account is not associated with any hospital. Please contact administrator.')
            return redirect('accounts:login')


class ActivityLogMiddleware(MiddlewareMixin):
    """Middleware to log user activities"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):
        # Skip logging for certain paths
        skip_paths = [
            '/static/',
            '/media/',
            '/admin/jsi18n/',
            '/api/notifications/',
            '/favicon.ico',
        ]
        
        if any(request.path.startswith(path) for path in skip_paths):
            return None
            
        # Store request start time
        request.start_time = timezone.now()
        return None
    
    def process_response(self, request, response):
        # Only log for authenticated users with hospital
        if not (hasattr(request, 'user') and request.user.is_authenticated and hasattr(request, 'hospital')):
            return response
            
        # Skip logging for GET requests to certain endpoints
        if request.method == 'GET' and any(request.path.startswith(path) for path in ['/api/', '/static/', '/media/']):
            return response
            
        # Log significant activities
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            self._log_activity(request, response)
            
        return response
    
    def _log_activity(self, request, response):
        """Log user activity"""
        try:
            # Get IP address
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0]
            else:
                ip_address = request.META.get('REMOTE_ADDR', '0.0.0.0')
            
            # Determine action based on method and response
            action_map = {
                'POST': 'CREATE' if response.status_code in [201, 302] else 'CREATE_FAILED',
                'PUT': 'UPDATE' if response.status_code in [200, 202] else 'UPDATE_FAILED',
                'PATCH': 'UPDATE' if response.status_code in [200, 202] else 'UPDATE_FAILED',
                'DELETE': 'DELETE' if response.status_code in [200, 204] else 'DELETE_FAILED',
            }
            
            action = action_map.get(request.method, 'UNKNOWN')
            
            # Extract model name from path
            path_parts = request.path.strip('/').split('/')
            model_name = path_parts[0] if path_parts else 'unknown'
            
            # Create activity log
            ActivityLog.objects.create(
                hospital=request.hospital,
                user=request.user,
                action=action,
                model_name=model_name.title(),
                object_repr=f"{request.method} {request.path}",
                ip_address=ip_address,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
            )
            
        except Exception as e:
            # Don't let logging errors break the request
            pass


class SubscriptionMiddleware(MiddlewareMixin):
    """Middleware to check hospital subscription status"""
    
    def process_request(self, request):
        # Skip for certain paths
        skip_paths = [
            '/admin/',
            '/api/auth/',
            '/auth/',
            '/static/',
            '/media/',
            '/subscription/',
        ]
        
        if any(request.path.startswith(path) for path in skip_paths):
            return None
            
        # Skip for unauthenticated users
        if not request.user.is_authenticated:
            return None
            
        # Skip for superusers
        if request.user.is_superuser or request.user.role == 'SUPERADMIN':
            return None
            
        # Check hospital subscription
        if hasattr(request, 'hospital') and request.hospital:
            if not request.hospital.is_subscription_active():
                if request.path != '/subscription/expired/':
                    return redirect('/subscription/expired/')
                    
        return None


class SecurityHeadersMiddleware(MiddlewareMixin):
    """Add security headers to responses"""
    
    def process_response(self, request, response):
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Add CSP header for non-admin pages
        if not request.path.startswith('/admin/'):
            response['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self';"
            )
            
        return response


class RateLimitMiddleware(MiddlewareMixin):
    """Simple rate limiting middleware"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.rate_limit_cache = {}
        super().__init__(get_response)
    
    def process_request(self, request):
        # Skip rate limiting for certain paths
        skip_paths = ['/static/', '/media/', '/admin/']
        if any(request.path.startswith(path) for path in skip_paths):
            return None
            
        # Get client IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            client_ip = x_forwarded_for.split(',')[0]
        else:
            client_ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
        
        # Simple rate limiting (100 requests per minute per IP)
        from django.core.cache import cache
        from django.http import HttpResponse
        
        current_time = timezone.now()
        cache_key = f"rate_limit_{client_ip}"
        
        # Get current request count
        request_data = cache.get(cache_key, {'count': 0, 'window_start': current_time})
        
        # Reset if window has passed (1 minute)
        if (current_time - request_data['window_start']).total_seconds() > 60:
            request_data = {'count': 1, 'window_start': current_time}
        else:
            request_data['count'] += 1
        
        # Check if limit exceeded
        if request_data['count'] > 100:
            return HttpResponse("Rate limit exceeded. Please try again later.", status=429)
        
        # Update cache
        cache.set(cache_key, request_data, 60)  # Cache for 1 minute
        
        return None


class LoginAttemptMiddleware(MiddlewareMixin):
    """Track failed login attempts and lockout accounts"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):
        # Only monitor login attempts
        if request.path != '/auth/login/' or request.method != 'POST':
            return None
            
        # Get client IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            client_ip = x_forwarded_for.split(',')[0]
        else:
            client_ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
        
        from django.core.cache import cache
        from django.http import HttpResponseForbidden
        
        # Check if IP is locked out
        lockout_key = f"login_lockout_{client_ip}"
        if cache.get(lockout_key):
            return HttpResponseForbidden("Too many failed login attempts. Please try again later.")
        
        return None
    
    def process_response(self, request, response):
        # Only monitor login responses
        if request.path != '/auth/login/' or request.method != 'POST':
            return response
            
        # Get client IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            client_ip = x_forwarded_for.split(',')[0]
        else:
            client_ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
        
        from django.core.cache import cache
        from django.conf import settings
        
        # Track failed attempts (redirect or error response)
        if response.status_code in [302, 200] and 'error' in str(response.content):
            attempt_key = f"login_attempts_{client_ip}"
            attempts = cache.get(attempt_key, 0) + 1
            
            if attempts >= getattr(settings, 'LOGIN_ATTEMPT_LIMIT', 5):
                # Lock out for timeout period
                lockout_key = f"login_lockout_{client_ip}"
                timeout = getattr(settings, 'LOGIN_ATTEMPT_TIMEOUT', 300)
                cache.set(lockout_key, True, timeout)
                cache.delete(attempt_key)
            else:
                cache.set(attempt_key, attempts, 3600)  # Track for 1 hour
        
        # Clear attempts on successful login
        elif response.status_code == 302 and '/dashboard/' in response.get('Location', ''):
            attempt_key = f"login_attempts_{client_ip}"
            cache.delete(attempt_key)
        
        return response


class HospitalSelectionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # List of URL names that require a hospital to be selected
        required_url_names = [
            'patients:patient_create',
            'doctors:doctor_create',
            'appointments:appointment_create',
            'laboratory:test_create',
            'radiology:radiology_test_create',
            'billing:bill_create',
            # Add other URL names for creation pages here
        ]

        # List of URL path prefixes that require a hospital to be selected
        required_path_prefixes = [
            '/patient/add/',
            '/doctor/add/',
            '/appointment/add/',
            '/lab/add/',
            '/radiology/add/',
            '/bill/add/',
        ]

        # Check if the current URL requires hospital selection
        resolver_match = request.resolver_match
        if resolver_match:
            url_name = resolver_match.view_name
            path = request.path_info

            requires_hospital = (
                url_name in required_url_names or
                any(path.startswith(prefix) for prefix in required_path_prefixes)
            )

            if requires_hospital and not request.session.get('selected_hospital_code'):
                # Store the intended destination
                request.session['next_url'] = request.path
                # Redirect to the hospital selection page
                return redirect(reverse('tenants:hospital_selection'))

        response = self.get_response(request)
        return response


class SessionTimeoutMiddleware(MiddlewareMixin):
    """
    Middleware to automatically log out users after a period of inactivity.
    """

    def process_request(self, request):
        # Skip for admin and API endpoints
        if request.path.startswith('/admin/') or request.path.startswith('/api/'):
            return None

        # Skip for unauthenticated users
        if not request.user.is_authenticated:
            return None

        # Check for session timeout
        idle_timeout = 15 * 60  # 15 minutes
        last_activity = request.session.get('last_activity')
        if last_activity:
            elapsed_time = timezone.now() - last_activity
            if elapsed_time.total_seconds() > idle_timeout:
                # Log out the user and clear the session
                logout(request)
                return None  # Redirect to login page handled by Django

        # Update last activity time
        request.session['last_activity'] = timezone.now()
        return None


class AdminLoginRedirectMiddleware(MiddlewareMixin):
    """
    Middleware to handle admin login redirects properly
    """
    def process_response(self, request, response):
        # Check if this is a redirect after admin login to dashboard
        if (response.status_code == 302 and 
            request.path == '/admin/login/' and 
            response.get('Location') == '/dashboard/' and
            request.user.is_authenticated and 
            (request.user.is_staff or request.user.is_superuser)):
            
            # Redirect to admin index instead of dashboard  
            from django.http import HttpResponseRedirect
            return HttpResponseRedirect('/admin/')
            
        return response
