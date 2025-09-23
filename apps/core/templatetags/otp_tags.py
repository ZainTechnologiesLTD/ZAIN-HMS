from django import template
from django_otp import user_has_device

register = template.Library()

@register.filter
def otp_device(user):
    """Return True if user has at least one confirmed OTP device."""
    try:
        return user_has_device(user)
    except Exception:
        return False
