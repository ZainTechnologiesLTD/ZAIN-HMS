# Communication template tags and filters
from django import template
from django.utils import timezone
from datetime import timedelta
from ..models import CommunicationLog

register = template.Library()


@register.filter
def communication_status(appointment, channel=None):
    """Get latest communication status for appointment"""
    try:
        query = appointment.communications.all()
        if channel:
            query = query.filter(channel=channel)
        
        latest = query.order_by('-sent_at').first()
        if not latest:
            return {'status': 'none', 'icon': 'bi-dash', 'color': 'text-muted'}
        
        status_map = {
            'sent': {'status': 'sent', 'icon': 'bi-check', 'color': 'text-primary'},
            'delivered': {'status': 'delivered', 'icon': 'bi-check2', 'color': 'text-success'},
            'read': {'status': 'read', 'icon': 'bi-check2-all', 'color': 'text-success'},
            'failed': {'status': 'failed', 'icon': 'bi-x-circle', 'color': 'text-danger'},
            'pending': {'status': 'pending', 'icon': 'bi-clock', 'color': 'text-warning'},
        }
        
        return status_map.get(latest.status, status_map['pending'])
        
    except Exception:
        return {'status': 'error', 'icon': 'bi-exclamation-triangle', 'color': 'text-danger'}


@register.filter
def last_communication_time(appointment):
    """Get time of last communication"""
    try:
        latest = appointment.communications.order_by('-sent_at').first()
        if not latest:
            return None
        
        now = timezone.now()
        diff = now - latest.sent_at
        
        if diff.days > 0:
            return f"{diff.days}d ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours}h ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes}m ago"
        else:
            return "Just now"
            
    except Exception:
        return None


@register.inclusion_tag('communications/status_badges.html')
def communication_badges(appointment):
    """Render communication status badges"""
    channels = ['whatsapp', 'telegram', 'viber', 'email']
    statuses = {}
    
    for channel in channels:
        statuses[channel] = communication_status(appointment, channel)
    # Determine if any channel has an active (non-"none") status so template can decide to show placeholders
    has_activity = any(s.get('status') not in ('none', 'error') for s in statuses.values())

    return {
        'appointment': appointment,
        'statuses': statuses,
        'last_time': last_communication_time(appointment),
        'has_activity': has_activity,
    }


@register.simple_tag
def communication_count(appointment, status=None):
    """Count communications for appointment"""
    try:
        query = appointment.communications.all()
        if status:
            query = query.filter(status=status)
        return query.count()
    except Exception:
        return 0
