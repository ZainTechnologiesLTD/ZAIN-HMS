"""
Enterprise-Grade Security Middleware for ZAIN HMS
Provides comprehensive authentication, authorization, and audit logging
"""

import logging
import json
import time
from datetime import datetime, timedelta
from django.http import HttpResponseRedirect, JsonResponse, HttpResponseForbidden
from django.urls import reverse
from django.contrib.auth import logout
from django.contrib import messages
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache
from django.contrib.sessions.models import Session
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone
import hashlib
import socket


# Security audit logger
security_logger = logging.getLogger('zain_hms.security')


class EnterpriseSecurityMiddleware(MiddlewareMixin):
    """
    Enterprise-grade security middleware that provides:
    1. Centralized authentication enforcement
    2. Role-based access control (RBAC)
    3. Session security and timeout
    4. IP-based access control
    5. Brute force protection
    6. Comprehensive audit logging
    7. Security headers
    """
    
    # Sensitive paths that require additional security
    SENSITIVE_PATHS = [
        '/patients/',
        '/appointments/',
        '/billing/',
        '/reports/',
        '/staff/',
        '/doctors/',
        '/pharmacy/',
        '/laboratory/',
        '/radiology/',
        '/surgery/',
        '/emr/',
        '/emergency/',
    ]
    
    # Role-based access control matrix
    RBAC_MATRIX = {
        'SUPERADMIN': ['*'],  # Access to everything
        'HOSPITAL_ADMIN': [
            'patients/', 'appointments/', 'billing/', 'reports/',
            'staff/', 'doctors/', 'pharmacy/', 'laboratory/',
            'radiology/', 'surgery/', 'dashboard/', 'settings/'
        ],
        'DOCTOR': [
            'patients/', 'appointments/', 'emr/', 'reports/',
            'laboratory/', 'radiology/', 'pharmacy/', 'dashboard/'
        ],
        'NURSE': [
            'patients/', 'appointments/', 'emr/', 'emergency/',
            'laboratory/', 'pharmacy/', 'dashboard/'
        ],
        'STAFF': [
            'patients/', 'appointments/', 'billing/', 'dashboard/'
        ],
        'RECEPTIONIST': [
            'patients/', 'appointments/', 'dashboard/'
        ],
        'PATIENT': [
            'patients/profile/', 'appointments/my/', 'reports/my/', 'dashboard/'
        ]
    }
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Build language-prefixed public paths dynamically
        self._build_public_paths()
        super().__init__(get_response)
    
    def _build_public_paths(self):
        """Build public paths with all supported language prefixes"""
        base_public_paths = [
            '/accounts/login/',
            '/accounts/register/', 
            '/accounts/password-reset/',
            '/accounts/activate/',
            '/',  # Landing page
        ]
        
        # Get supported languages from settings
        from django.conf import settings
        supported_languages = [lang[0] for lang in settings.LANGUAGES]
        
        # Build the complete PUBLIC_PATHS list
        self.PUBLIC_PATHS = [
            '/static/',
            '/media/',
            '/admin/',  # Django admin has its own auth
            '/api/public/',
            '/favicon.ico',
        ]
        
        # Add base paths
        self.PUBLIC_PATHS.extend(base_public_paths)
        
        # Add language-prefixed paths
        for lang in supported_languages:
            for path in base_public_paths:
                if path == '/':
                    self.PUBLIC_PATHS.append(f'/{lang}/')
                else:
                    self.PUBLIC_PATHS.append(f'/{lang}{path}')
    
    
    def process_request(self, request):
        """Process incoming request for security validation"""
        
        # Add security headers
        self._add_security_headers(request)
        
        # Log access attempt
        self._log_access_attempt(request)
        
        # Check if path is public
        if self._is_public_path(request.path):
            return None
        
        # Check authentication
        if not self._is_authenticated(request):
            return self._handle_unauthenticated_access(request)
        
        # Check session security
        if not self._is_session_valid(request):
            return self._handle_invalid_session(request)
        
        # Check authorization
        if not self._is_authorized(request):
            return self._handle_unauthorized_access(request)
        
        # Check brute force protection
        if self._is_brute_force_attack(request):
            return self._handle_brute_force(request)
        
        # Update last activity
        self._update_last_activity(request)
        
        return None
    
    def process_response(self, request, response):
        """Process outgoing response"""
        
        # Add security headers to response
        response['X-Frame-Options'] = 'DENY'
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://unpkg.com https://cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "img-src 'self' data: https:; "
            "font-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com;"
        )
        
        # Log response
        self._log_response(request, response)
        
        return response
    
    def _is_public_path(self, path):
        """Check if path is in public paths list"""
        return any(path.startswith(public_path) for public_path in self.PUBLIC_PATHS)
    
    def _is_authenticated(self, request):
        """Check if user is authenticated"""
        return request.user and request.user.is_authenticated
    
    def _is_session_valid(self, request):
        """Validate session security"""
        if not hasattr(request, 'session'):
            return False
        
        # Check session timeout
        last_activity = request.session.get('last_activity')
        if last_activity:
            session_timeout = getattr(settings, 'SESSION_TIMEOUT', 3600)  # 1 hour default
            if time.time() - last_activity > session_timeout:
                security_logger.warning(
                    f"Session timeout for user {request.user.username} from IP {self._get_client_ip(request)}"
                )
                return False
        
        # Check IP consistency (prevent session hijacking)
        session_ip = request.session.get('session_ip')
        current_ip = self._get_client_ip(request)
        
        if session_ip and session_ip != current_ip:
            security_logger.critical(
                f"Session hijacking attempt detected! User: {request.user.username}, "
                f"Original IP: {session_ip}, Current IP: {current_ip}"
            )
            return False
        
        # Set IP if not set
        if not session_ip:
            request.session['session_ip'] = current_ip
        
        return True
    
    def _is_authorized(self, request):
        """Check role-based authorization"""
        if not hasattr(request.user, 'role'):
            security_logger.error(f"User {request.user.username} has no role assigned")
            return False
        
        user_role = request.user.role
        path = request.path.lstrip('/')
        
        # Remove language prefix if exists
        if path.startswith(('en/', 'ar/', 'es/', 'fr/')):
            path = '/'.join(path.split('/')[1:])
        
        # Superadmin has access to everything
        if user_role == 'SUPERADMIN':
            return True
        
        # Check role-based access
        allowed_paths = self.RBAC_MATRIX.get(user_role, [])
        
        # Check if user has access to this path
        for allowed_path in allowed_paths:
            if allowed_path == '*' or path.startswith(allowed_path):
                return True
        
        security_logger.warning(
            f"Unauthorized access attempt: User {request.user.username} "
            f"(Role: {user_role}) tried to access {path} from IP {self._get_client_ip(request)}"
        )
        return False
    
    def _is_brute_force_attack(self, request):
        """Check for brute force attacks"""
        client_ip = self._get_client_ip(request)
        cache_key = f"failed_attempts_{client_ip}"
        
        failed_attempts = cache.get(cache_key, 0)
        max_attempts = getattr(settings, 'MAX_FAILED_ATTEMPTS', 5)
        
        if failed_attempts >= max_attempts:
            security_logger.critical(
                f"Brute force attack detected from IP {client_ip} - {failed_attempts} failed attempts"
            )
            return True
        
        return False
    
    def _handle_unauthenticated_access(self, request):
        """Handle unauthenticated access attempts"""
        security_logger.info(
            f"Unauthenticated access attempt to {request.path} from IP {self._get_client_ip(request)}"
        )
        
        if request.is_ajax():
            return JsonResponse({
                'error': 'Authentication required',
                'redirect': reverse('accounts:login')
            }, status=401)
        
        messages.warning(request, 'Please log in to access this page.')
        return HttpResponseRedirect(f"{reverse('accounts:login')}?next={request.path}")
    
    def _handle_invalid_session(self, request):
        """Handle invalid session"""
        logout(request)
        messages.error(request, 'Your session has expired. Please log in again.')
        
        if request.is_ajax():
            return JsonResponse({
                'error': 'Session expired',
                'redirect': reverse('accounts:login')
            }, status=401)
        
        return HttpResponseRedirect(reverse('accounts:login'))
    
    def _handle_unauthorized_access(self, request):
        """Handle unauthorized access attempts"""
        if request.is_ajax():
            return JsonResponse({
                'error': 'Access denied - Insufficient permissions'
            }, status=403)
        
        messages.error(request, 'You do not have permission to access this page.')
        return HttpResponseForbidden('Access Denied - Insufficient Permissions')
    
    def _handle_brute_force(self, request):
        """Handle brute force attacks"""
        if request.is_ajax():
            return JsonResponse({
                'error': 'Too many failed attempts. Please try again later.'
            }, status=429)
        
        return HttpResponseForbidden('Too many failed attempts. Access temporarily blocked.')
    
    def _update_last_activity(self, request):
        """Update user's last activity timestamp"""
        if hasattr(request, 'session'):
            request.session['last_activity'] = time.time()
    
    def _add_security_headers(self, request):
        """Add security-related request headers"""
        request.META['HTTP_X_ZAIN_HMS_VERSION'] = '2.5.1'
        request.META['HTTP_X_REQUEST_ID'] = hashlib.md5(
            f"{time.time()}{self._get_client_ip(request)}".encode()
        ).hexdigest()[:16]
    
    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        return ip
    
    def _log_access_attempt(self, request):
        """Log access attempt with comprehensive details"""
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'ip': self._get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', 'unknown'),
            'method': request.method,
            'path': request.path,
            'user': request.user.username if hasattr(request.user, 'username') else 'anonymous',
            'user_role': getattr(request.user, 'role', 'unknown') if hasattr(request.user, 'role') else 'anonymous',
            'session_key': request.session.session_key if hasattr(request, 'session') else 'none',
            'request_id': request.META.get('HTTP_X_REQUEST_ID', 'unknown')
        }
        
        security_logger.info(f"ACCESS_ATTEMPT: {json.dumps(log_data)}")
    
    def _log_response(self, request, response):
        """Log response details"""
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'request_id': request.META.get('HTTP_X_REQUEST_ID', 'unknown'),
            'status_code': response.status_code,
            'user': request.user.username if hasattr(request.user, 'username') else 'anonymous',
            'path': request.path,
            'processing_time': getattr(response, 'processing_time', 0)
        }
        
        if response.status_code >= 400:
            security_logger.warning(f"ERROR_RESPONSE: {json.dumps(log_data)}")
        else:
            security_logger.debug(f"SUCCESS_RESPONSE: {json.dumps(log_data)}")


class LoginAttemptMiddleware(MiddlewareMixin):
    """Track and limit login attempts"""
    
    def process_request(self, request):
        if request.path == reverse('accounts:login') and request.method == 'POST':
            client_ip = self._get_client_ip(request)
            cache_key = f"login_attempts_{client_ip}"
            
            # Get current attempts
            attempts = cache.get(cache_key, 0)
            max_attempts = getattr(settings, 'MAX_LOGIN_ATTEMPTS', 3)
            
            if attempts >= max_attempts:
                security_logger.critical(
                    f"Login brute force attempt blocked from IP {client_ip}"
                )
                messages.error(request, 'Too many failed login attempts. Please try again later.')
                return HttpResponseRedirect(reverse('accounts:login'))
        
        return None
    
    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        return ip