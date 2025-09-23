from django import template
from django.contrib.admin.views.main import ChangeList
from django.contrib.admin import AdminSite
from django.apps import apps
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

register = template.Library()

@register.simple_tag(takes_context=True)
def get_admin_app_list(context):
    """Get the admin app list for the current user."""
    request = context['request']
    user = request.user
    
    if not user.is_authenticated:
        return []
    
    admin_site = AdminSite()
    app_list = admin_site.get_app_list(request)
    
    return app_list
