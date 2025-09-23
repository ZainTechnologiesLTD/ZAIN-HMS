# apps/core/geo_security_middleware.py
"""
Geographic security middleware for country-based access control
Implements IP country validation against hospital country policy
"""
import logging
import requests
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth import logout
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class CountrySecurityMiddleware:
    """
    Middleware to enforce country-based access control policy:
    1. Detect user's public IP and country
    2. Compare with hospital's registered country
    3. Block access with warning if countries don't match
    4. Allow override for super admins
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Paths that don't require country validation
        self.exempt_paths = [
            '/admin/login/',
            '/admin/logout/',
            '/static/',
            '/media/',
            '/api/health/',
            '/country-access-denied/',
            '/admin/country-override/',
        ]
        
        # IP geolocation services (fallback chain)
        self.geo_services = [
            {
                'name': 'ipapi',
                'url': 'http://ip-api.com/json/{ip}',
                'country_field': 'country'
            },
            {
                'name': 'ipinfo',
                'url': 'https://ipinfo.io/{ip}/json',
                'country_field': 'country'
            },
            {
                'name': 'geoplugin',
                'url': 'http://www.geoplugin.net/json.gp?ip={ip}',
                'country_field': 'geoplugin_countryName'
            }
        ]

    def __call__(self, request):
        # Skip middleware for exempt paths
        if any(request.path.startswith(path) for path in self.exempt_paths):
            return self.get_response(request)
        
        # Skip for unauthenticated users
        if not request.user.is_authenticated:
            return self.get_response(request)
        
        # Skip for superusers (can override country restrictions)
        if request.user.is_superuser:
            return self.get_response(request)
        
        # Get user's current hospital
        hospital = self._get_user_hospital(request)
        if not hospital:
            return self.get_response(request)
        
        # Get user's IP country
        user_country = self._get_user_country(request)
        if not user_country:
            logger.warning(f"Could not determine country for user {request.user.username} from IP")
            # Allow access but log the issue
            return self.get_response(request)
        
        # Validate country match
        if not self._validate_country_access(hospital, user_country):
            logger.warning(
                f"Country access violation: User {request.user.username} "
                f"from {user_country} trying to access {hospital.name} "
                f"registered in {hospital.country}"
            )
            return self._handle_country_violation(request, hospital, user_country)
        
        return self.get_response(request)

    def _get_user_hospital(self, request):
        """Get the hospital associated with current user/session"""
        try:
            # Try to get hospital from user profile
            if hasattr(request.user, 'hospital_admin_user'):
                return request.user.hospital_admin_user.hospital
            
            # Try to get from subdomain
            subdomain = self._extract_subdomain(request)
            if subdomain:
            
            return None
        except Exception as e:
            logger.error(f"Error getting user hospital: {e}")
            return None

    def _extract_subdomain(self, request):
        """Extract subdomain from request host"""
        host = request.get_host().lower()
        
        # Development pattern (subdomain.localhost:8000)
        if 'localhost' in host:
            parts = host.split('.')
            if len(parts) >= 2 and parts[0] != 'www':
                return parts[0]
        
        # Production pattern (subdomain.domain.com)
        parts = host.split('.')
        if len(parts) >= 3 and parts[0] != 'www':
            return parts[0]
        
        return None

    def _get_user_country(self, request):
        """Get user's country from IP address with caching"""
        user_ip = self._get_client_ip(request)
        
        # Skip local IPs
        if self._is_local_ip(user_ip):
            return None
        
        # Check cache first
        cache_key = f"ip_country_{user_ip}"
        cached_country = cache.get(cache_key)
        if cached_country:
            return cached_country
        
        # Try each geolocation service
        for service in self.geo_services:
            try:
                country = self._get_country_from_service(user_ip, service)
                if country:
                    # Cache for 24 hours
                    cache.set(cache_key, country, 86400)
                    return country
            except Exception as e:
                logger.warning(f"Geolocation service {service['name']} failed: {e}")
                continue
        
        return None

    def _get_client_ip(self, request):
        """Extract client IP from request headers"""
        # Check for forwarded IP (behind proxy/load balancer)
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        
        # Check for real IP header
        x_real_ip = request.META.get('HTTP_X_REAL_IP')
        if x_real_ip:
            return x_real_ip
        
        # Fallback to REMOTE_ADDR
        return request.META.get('REMOTE_ADDR', '127.0.0.1')

    def _is_local_ip(self, ip):
        """Check if IP is local/private"""
        local_patterns = [
            '127.', '10.', '192.168.', '172.16.', '172.17.',
            '172.18.', '172.19.', '172.20.', '172.21.',
            '172.22.', '172.23.', '172.24.', '172.25.',
            '172.26.', '172.27.', '172.28.', '172.29.',
            '172.30.', '172.31.', 'localhost', '0.0.0.0'
        ]
        return any(ip.startswith(pattern) for pattern in local_patterns)

    def _get_country_from_service(self, ip, service):
        """Get country from specific geolocation service"""
        url = service['url'].format(ip=ip)
        
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        
        data = response.json()
        country = data.get(service['country_field'])
        
        # Handle different response formats
        if country and country.lower() not in ['unknown', 'n/a', '', 'reserved']:
            return country.strip()
        
        return None

    def _validate_country_access(self, hospital, user_country):
        """Validate if user country matches hospital country"""
        if not hospital.country or not user_country:
            return True  # Allow access if country data is missing
        
        # Normalize country names for comparison
        hospital_country = hospital.country.lower().strip()
        user_country_normalized = user_country.lower().strip()
        
        # Direct match
        if hospital_country == user_country_normalized:
            return True
        
        # Common country name variations
        country_aliases = {
            'usa': ['united states', 'america', 'us'],
            'uk': ['united kingdom', 'britain', 'england'],
            'uae': ['united arab emirates', 'emirates'],
            # Add more aliases as needed
        }
        
        # Check aliases
        for canonical, aliases in country_aliases.items():
            if hospital_country in [canonical] + aliases:
                if user_country_normalized in [canonical] + aliases:
                    return True
        
        return False

    def _handle_country_violation(self, request, hospital, user_country):
        """Handle country access violation"""
        # Log security event
        logger.security(
            f"COUNTRY_ACCESS_VIOLATION: User {request.user.username} "
            f"from {user_country} attempted to access {hospital.name} "
            f"(registered in {hospital.country}) from IP {self._get_client_ip(request)}"
        )
        
        # Add security warning message
        messages.error(
            request,
            f"⚠️ Access Denied: Your location ({user_country}) doesn't match "
            f"the registered country for {hospital.name} ({hospital.country}). "
            f"This access attempt has been logged for security purposes."
        )
        
        # Logout user for security
        logout(request)
        
        # Redirect to custom error page
        return render(request, 'admin/country_access_denied.html', {
            'hospital': hospital,
            'user_country': user_country,
            'hospital_country': hospital.country,
            'support_email': getattr(settings, 'SECURITY_EMAIL', 'security@zainhms.com')
        })
