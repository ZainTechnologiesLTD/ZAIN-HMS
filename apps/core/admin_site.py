# apps/core/admin_site.py
from django.contrib.admin import AdminSite
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.http import HttpResponseRedirect


class ZainAdminSite(AdminSite):
    """Custom Admin Site for ZAIN HMS with proper redirect handling"""
    
    site_header = "ZAIN HMS Administration"
    site_title = "ZAIN HMS Admin"
    index_title = "Welcome to ZAIN Hospital Management System"
    
    def login(self, request, extra_context=None):
        """
        Handle admin login with custom redirect logic
        """
        # If user is already authenticated and is staff, redirect to admin index
        if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
            return HttpResponseRedirect(self.get_urls()[0].pattern.regex.pattern.replace('^', '/').replace('$', ''))
        
        # Otherwise, use default login behavior
        return super().login(request, extra_context)
    
    def get_urls(self):
        """Override to ensure admin URLs are properly configured"""
        from django.urls import path
        from django.contrib.admin.views.decorators import staff_member_required
        
        # Get default admin URLs
        urls = super().get_urls()
        
        # Add custom admin index redirect
        custom_urls = [
            path('', self.admin_view(self.index), name='index'),
        ]
        
        return custom_urls + urls
        
    def index(self, request, extra_context=None):
        """
        Custom admin index that ensures we stay in admin interface
        """
        # Ensure user is staff or superuser
        if not (request.user.is_staff or request.user.is_superuser):
            return redirect('/admin/login/')
            
        # Use default admin index
        return super().index(request, extra_context)


# Create instance of custom admin site
admin_site = ZainAdminSite(name='zain_admin')
