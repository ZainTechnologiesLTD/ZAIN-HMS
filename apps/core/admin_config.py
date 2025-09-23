# apps/core/admin_config.py
from django.contrib import admin
from django.contrib.admin import AdminSite
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib.auth import logout
from django.contrib import messages
from django.shortcuts import redirect


class CustomAdminSite(AdminSite):
    """
    Custom admin site that handles logout properly
    """
    site_header = 'HMS Hospital Management System'
    site_title = 'HMS Admin'
    index_title = 'Hospital Management Administration'
    
    def logout(self, request, extra_context=None):
        """
        Custom logout that redirects to admin login instead of user login
        """
        logout(request)
        messages.success(request, 'You have been successfully logged out from the admin interface.')
        return HttpResponseRedirect(reverse('admin:login'))


# Create custom admin site instance
admin_site = CustomAdminSite(name='admin')
