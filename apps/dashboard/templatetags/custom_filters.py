# In your app/templatetags/custom_filters.py
from django import template

register = template.Library()

@register.filter(name='get_title')
def get_title(user):
    if user.groups.filter(name='Admin').exists() and user.groups.filter(name='Doctor').exists():
        return 'Admin'
    elif user.groups.filter(name='Doctor').exists():
        return 'Dr.'
    elif user.groups.filter(name='Nurse').exists():
        return 'Nurse'
    elif user.groups.filter(name='staff').exists():
        return 'Staff'
    return ''