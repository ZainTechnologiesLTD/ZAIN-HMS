# ZAIN HMS Security Middleware Suite
# Healthcare-grade security middleware for HIPAA compliance - Single Hospital System

import logging
import hashlib
import json
import time
from datetime import datetime, timedelta
from ipaddress import ip_address, ip_network
from django.conf import settings
from django.contrib.auth import logout
from django.core.cache import cache
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import User
from django.core.exceptions import SuspiciousOperation
from django.utils import timezone
from django.contrib import messages
from cryptography.fernet import Fernet
import os
from django_otp import user_has_device

# Configure audit logger
audit_logger = logging.getLogger('zain_hms.audit')
security_logger = logging.getLogger('django.security')

class SecurityAuditMiddleware(MiddlewareMixin):
    """
    Comprehensive security audit middleware for HIPAA compliance
    Logs all access attempts and security-relevant events
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.sensitive_paths = [
            '/patients/', '/medical-records/', '/admin/', 
            '/api/patient/', '/reports/', '/billing/'
        ]
        
    def process_request(self, request):
        # Log all requests for audit trail
        user_id = getattr(request.user, 'id', 'anonymous') if hasattr(request, 'user') else 'anonymous'
        
        audit_data = {
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id,
            'ip_address': self.get_client_ip(request),
            'method': request.method,
            'path': request.path,
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'referer': request.META.get('HTTP_REFERER', ''),
        }
        
        # Check if accessing sensitive healthcare data
        is_sensitive = any(path in request.path for path in self.sensitive_paths)
        
        if is_sensitive:
            audit_logger.info(
                f"SENSITIVE_ACCESS path={request.path} user={user_id} "
                f"ip={audit_data['ip_address']} method={request.method}"
            )
            
        # Store request start time for performance monitoring
        request._security_start_time = time.time()
        
        return None
        
    def process_response(self, request, response):
        # Calculate request processing time
        if hasattr(request, '_security_start_time'):
            processing_time = time.time() - request._security_start_time
            
            # Log slow requests (potential DoS attempts)
            if processing_time > 5.0:  # 5 seconds threshold
                security_logger.warning(
                    f"SLOW_REQUEST path={request.path} time={processing_time:.2f}s "
                    f"ip={self.get_client_ip(request)} status={response.status_code}"
                )
                
        # Log failed authentication attempts
        if response.status_code in [401, 403, 404]:
            security_logger.warning(
                f"ACCESS_DENIED status={response.status_code} path={request.path} "
                f"ip={self.get_client_ip(request)} user={getattr(request.user, 'id', 'anonymous')}"
            )
            
        return response
        
    def get_client_ip(self, request):
        """Get the real client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class BruteForceProtectionMiddleware(MiddlewareMixin):
    """
    Advanced brute force protection for healthcare systems
    Implements progressive delays and IP blocking
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.max_attempts = getattr(settings, 'LOGIN_ATTEMPTS_LIMIT', 5)
        self.lockout_duration = getattr(settings, 'LOGIN_LOCKOUT_DURATION', 900)  # 15 minutes
        
    def process_request(self, request):
        # Only check login attempts on authentication endpoints
        if not self._is_auth_endpoint(request.path):
            return None
            
        client_ip = self._get_client_ip(request)
        
        # Check if IP is currently blocked
        if self._is_ip_blocked(client_ip):
            security_logger.error(
                f"BLOCKED_IP_ACCESS ip={client_ip} path={request.path} "
                f"reason=brute_force_protection"
            )
            return HttpResponseForbidden(
                "Access denied due to multiple failed login attempts. "
                "Please try again later."
            )
            
        # Check user-specific attempts if username provided
        username = request.POST.get('username') or request.POST.get('email')
        if username and self._is_user_locked(username):
            security_logger.error(
                f"LOCKED_USER_ACCESS user={username} ip={client_ip} "
                f"reason=brute_force_protection"
            )
            return HttpResponseForbidden(
                "Account temporarily locked due to multiple failed login attempts."
            )
            
        return None
        
    def process_response(self, request, response):
        # Track failed login attempts
        if self._is_auth_endpoint(request.path) and response.status_code in [401, 403]:
            client_ip = self._get_client_ip(request)
            username = request.POST.get('username') or request.POST.get('email')
            
            self._record_failed_attempt(client_ip, username)
            
        return response
        
    def _is_auth_endpoint(self, path):
        auth_endpoints = ['/accounts/login/', '/api/auth/', '/admin/login/']
        return any(endpoint in path for endpoint in auth_endpoints)
        
    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
        
    def _is_ip_blocked(self, ip):
        cache_key = f'failed_attempts_ip_{ip}'
        attempts = cache.get(cache_key, 0)
        return attempts >= self.max_attempts
        
    def _is_user_locked(self, username):
        cache_key = f'failed_attempts_user_{username}'
        attempts = cache.get(cache_key, 0)
        return attempts >= self.max_attempts
        
    def _record_failed_attempt(self, ip, username=None):
        # Record IP-based attempt
        ip_cache_key = f'failed_attempts_ip_{ip}'
        ip_attempts = cache.get(ip_cache_key, 0) + 1
        cache.set(ip_cache_key, ip_attempts, self.lockout_duration)
        
        # Record user-based attempt if username provided
        if username:
            user_cache_key = f'failed_attempts_user_{username}'
            user_attempts = cache.get(user_cache_key, 0) + 1
            cache.set(user_cache_key, user_attempts, self.lockout_duration)
            
        security_logger.warning(
            f"FAILED_LOGIN_ATTEMPT ip={ip} user={username} "
            f"ip_attempts={ip_attempts} lockout_time={self.lockout_duration}s"
        )


class IPWhitelistMiddleware(MiddlewareMixin):
    """
    IP whitelist middleware for admin and sensitive areas
    Supports both individual IPs and CIDR ranges
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.whitelist_enabled = getattr(settings, 'IP_WHITELIST_ENABLED', False)
        self.whitelisted_ips = getattr(settings, 'IP_WHITELIST', [])
        self.protected_paths = getattr(settings, 'IP_PROTECTED_PATHS', ['/admin/'])
        
    def process_request(self, request):
        if not self.whitelist_enabled:
            return None
            
        # Check if path needs IP protection
        needs_protection = any(
            protected_path in request.path 
            for protected_path in self.protected_paths
        )
        
        if not needs_protection:
            return None
            
        client_ip = self._get_client_ip(request)
        
        if not self._is_ip_allowed(client_ip):
            security_logger.error(
                f"IP_WHITELIST_VIOLATION ip={client_ip} path={request.path} "
                f"user={getattr(request.user, 'id', 'anonymous')}"
            )
            return HttpResponseForbidden("Access denied: IP not whitelisted")
            
        return None
        
    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
        
    def _is_ip_allowed(self, client_ip):
        try:
            client_ip_obj = ip_address(client_ip)
            for allowed_ip in self.whitelisted_ips:
                try:
                    # Try as network range first
                    if client_ip_obj in ip_network(allowed_ip, strict=False):
                        return True
                except ValueError:
                    # Try as individual IP
                    if client_ip_obj == ip_address(allowed_ip):
                        return True
        except ValueError:
            security_logger.error(f"INVALID_IP_FORMAT ip={client_ip}")
            return False
            
        return False


class HealthcareComplianceMiddleware(MiddlewareMixin):
    """
    HIPAA and healthcare compliance middleware
    Handles PHI access logging and compliance checks
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.phi_patterns = [
            'patient', 'medical', 'diagnosis', 'prescription', 
            'insurance', 'billing', 'treatment'
        ]
        
    def process_request(self, request):
        # Check for PHI access
        if self._contains_phi_access(request):
            if not request.user.is_authenticated:
                security_logger.error(
                    f"PHI_ACCESS_UNAUTHENTICATED path={request.path} "
                    f"ip={self._get_client_ip(request)}"
                )
                return HttpResponseForbidden("Authentication required for PHI access")
                
            # Log PHI access for HIPAA compliance
            audit_logger.info(
                f"PHI_ACCESS user={request.user.id} path={request.path} "
                f"ip={self._get_client_ip(request)} timestamp={datetime.now().isoformat()}"
            )
            
        return None
        
    def process_response(self, request, response):
        # Add security headers for healthcare compliance
        response['X-Healthcare-Compliance'] = 'HIPAA-Ready'
        response['X-PHI-Protection'] = 'Enabled'
        
        # Remove server information for security
        if 'Server' in response:
            del response['Server']
            
        return response
        
    def _contains_phi_access(self, request):
        path_lower = request.path.lower()
        return any(pattern in path_lower for pattern in self.phi_patterns)
        
    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class DataEncryptionMiddleware(MiddlewareMixin):
    """
    Data encryption middleware for sensitive healthcare data
    Handles automatic encryption/decryption of PHI fields
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.encryption_key = os.getenv('DATA_ENCRYPTION_KEY')
        if self.encryption_key:
            try:
                self.cipher_suite = Fernet(self.encryption_key.encode())
            except:
                self.cipher_suite = None
        else:
            self.cipher_suite = None
            
    def process_request(self, request):
        # Decrypt incoming encrypted data if needed
        if request.method == 'POST' and self.cipher_suite:
            encrypted_fields = request.POST.get('_encrypted_fields', '').split(',')
            for field in encrypted_fields:
                if field and field in request.POST:
                    try:
                        decrypted_data = self.cipher_suite.decrypt(
                            request.POST[field].encode()
                        ).decode()
                        request.POST._mutable = True
                        request.POST[field] = decrypted_data
                        request.POST._mutable = False
                    except Exception as e:
                        security_logger.error(
                            f"DECRYPTION_ERROR field={field} error={str(e)}"
                        )
                        
        return None
        
    def process_response(self, request, response):
        # Add data protection headers
        response['X-Data-Encryption'] = 'AES-256' if self.cipher_suite else 'None'
        return response


class SessionTimeoutMiddleware(MiddlewareMixin):
    """
    Healthcare-compliant session timeout middleware
    Implements aggressive timeout for HIPAA compliance
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.timeout_seconds = getattr(settings, 'SESSION_TIMEOUT', 3600)  # 1 hour
        
    def process_request(self, request):
        # Skip for admin and API endpoints
        if request.path.startswith('/admin/') or request.path.startswith('/api/'):
            return None

        # Skip for unauthenticated users
        if not request.user.is_authenticated:
            return None
            
        current_time = time.time()
        last_activity = request.session.get('last_activity')
        
        if last_activity:
            time_since_activity = current_time - last_activity
            
            if time_since_activity > self.timeout_seconds:
                # Log session timeout
                audit_logger.info(
                    f"SESSION_TIMEOUT user={request.user.id} "
                    f"inactive_time={time_since_activity:.0f}s "
                    f"ip={self._get_client_ip(request)}"
                )
                
                # Clear session and logout user
                logout(request)
                
                if request.headers.get('Content-Type') == 'application/json':
                    return JsonResponse({
                        'error': 'Session expired due to inactivity',
                        'redirect': '/accounts/login/'
                    }, status=401)
                else:
                    return redirect('/accounts/login/?timeout=1')
                    
        # Update last activity time
        request.session['last_activity'] = current_time
        
        return None
        
    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class EnforceTwoFactorMiddleware(MiddlewareMixin):
    """Redirect authenticated users without 2FA to setup page for protected paths."""
    
    def process_request(self, request):
        if not request.user.is_authenticated:
            return None
            
        path = request.path
        
        # Skip exclusions - handle internationalized URLs properly
        excluded_patterns = [
            '/core/2fa/',
            '/core/2fa/verify/',
            '/core/2fa/disable/',
            '/admin/', '/accounts/logout/', '/accounts/login/', '/static/', '/media/'
        ]
        
        # Also add language prefixed versions
        for pattern in excluded_patterns[:]:  # Copy list to avoid modification during iteration
            excluded_patterns.append(f'/en{pattern}')
            excluded_patterns.append(f'/ar{pattern}')
            excluded_patterns.append(f'/fr{pattern}')
            
        if any(path.startswith(p) for p in excluded_patterns):
            return None
            
        # Only enforce for staff / superusers (configurable)
        if (request.user.is_staff or request.user.is_superuser) and not user_has_device(request.user):
            request.session['post_2fa_redirect'] = path
            return redirect(reverse('core:setup_2fa'))
            
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
        # Only log for authenticated users
        if not (hasattr(request, 'user') and request.user.is_authenticated):
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
            
            # Log activity (you may want to create ActivityLog model for single hospital)
            audit_logger.info(
                f"USER_ACTIVITY user={request.user.id} action={action} "
                f"model={model_name.title()} path={request.path} "
                f"ip={ip_address} status={response.status_code}"
            )
            
        except Exception as e:
            # Don't let logging errors break the request
            security_logger.error(f"ACTIVITY_LOG_ERROR: {str(e)}")


class SecurityHeadersMiddleware(MiddlewareMixin):
    """Add security headers to responses"""
    
    def process_response(self, request, response):
        # If some view returned a non-HttpResponse (should not happen), just pass it through
        try:
            _ = response.__setitem__
        except Exception:
            return response

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
                "font-src 'self' data: https://fonts.gstatic.com https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self' https://cdn.jsdelivr.net https:;"
            )
            
        return response


class RateLimitMiddleware(MiddlewareMixin):
    """Simple rate limiting middleware"""
    
    def __init__(self, get_response):
        self.get_response = get_response
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
        if request.path != '/auth/login/':
            # Expose a flag to template for captcha requirement if threshold reached
            if request.method == 'GET':
                x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
                if x_forwarded_for:
                    client_ip = x_forwarded_for.split(',')[0]
                else:
                    client_ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
                attempt_key = f"login_attempts_{client_ip}"
                attempts = cache.get(attempt_key, 0)
                captcha_threshold = getattr(settings, 'LOGIN_CAPTCHA_THRESHOLD', 3)
                request.show_login_captcha = attempts >= captcha_threshold
            return None
            
        # Get client IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            client_ip = x_forwarded_for.split(',')[0]
        else:
            client_ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
        
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
        
        # Track failed attempts (redirect or error response)
        if response.status_code in [302, 200] and 'error' in str(response.content):
            attempt_key = f"login_attempts_{client_ip}"
            attempts = cache.get(attempt_key, 0) + 1
            captcha_threshold = getattr(settings, 'LOGIN_CAPTCHA_THRESHOLD', 3)
            
            # Mark need for captcha after threshold but before lockout
            if attempts >= captcha_threshold:
                cache.set(f"login_captcha_required_{client_ip}", True, 900)
            
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
            cache.delete(f"login_captcha_required_{client_ip}")
        
        return response


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


class HospitalContextMiddleware(MiddlewareMixin):
    """
    Middleware to set hospital context for single hospital system
    """
    def process_request(self, request):
        # For single hospital system, set the hospital context
        request.hospital = {
            'id': 'single-hospital',
            'name': 'ZAIN Hospital',
            'code': 'ZAIN001',
            'is_active': True
        }
        return None


class HospitalMiddleware(MiddlewareMixin):
    """
    Middleware for hospital-specific operations
    """
    def process_request(self, request):
        # Placeholder for hospital-specific middleware logic
        return None
