# apps/core/admin_views.py
from django.shortcuts import redirect
from django.contrib.auth import logout
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test

def is_staff_or_superuser(user):
    return user.is_staff or user.is_superuser

@user_passes_test(is_staff_or_superuser)
def admin_logout_view(request):
    """Custom logout view for admin users that redirects back to admin login"""
    if request.method == 'POST':
        logout(request)
        messages.success(request, 'You have been successfully logged out from the admin interface.')
        # Redirect to admin login instead of regular user login
        return redirect('/admin/login/')
    else:
        # If someone tries to access via GET, redirect to admin
        return redirect('/admin/')
