# apps/core/middleware.py
from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import redirect
from django.contrib.auth import logout
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from apps.accounts.models import Hospital
from apps.core.models import ActivityLog
import json
import uuid


class HospitalMiddleware(MiddlewareMixin):
    """Multi-tenant middleware to handle hospital-specific requests"""
    
    def process_request(self, request):
        # Skip for admin and API endpoints
        if request.path.startswith('/admin/') or request.path.startswith('/api/'):
            return None
            
        # Skip for unauthenticated users
        if not request.user.is_authenticated:
            return None
            
        # Super admin can access all hospitals
        if request.user.is_superuser or request.user.role == 'SUPERADMIN':
            return None
            
        # Set hospital for authenticated users
        if request.user.hospital:
            request.hospital = request.user.hospital
        else:
            # Redirect users without hospital assignment
            logout(request)
            messages.error(request, 'Your account is not associated with any hospital. Please contact administrator.')
            return redirect('accounts:login')
            
        return None


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
                "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
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
        now = timezone.now()
        minute_key = f"{client_ip}:{now.strftime('%Y-%m-%d-%H-%M')}"
        
        if minute_key in self.rate_limit_cache:
            self.rate_limit_cache[minute_key] += 1
            if self.rate_limit_cache[minute_key] > 100:
                return JsonResponse({'error': 'Rate limit exceeded'}, status=429)
        else:
            self.rate_limit_cache[minute_key] = 1
            
        # Clean old entries (keep only last 2 minutes)
        keys_to_delete = []
        for key in self.rate_limit_cache:
            if key.split(':')[1] < (now - timezone.timedelta(minutes=2)).strftime('%Y-%m-%d-%H-%M'):
                keys_to_delete.append(key)
        
        for key in keys_to_delete:
            del self.rate_limit_cache[key]
            
        return None
