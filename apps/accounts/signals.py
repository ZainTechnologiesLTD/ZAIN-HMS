from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
import logging
from apps.tenants.models import Tenant

logger = logging.getLogger(__name__)

@receiver(user_logged_in)
def persist_session_selected_hospital(sender, user, request, **kwargs):
    """When a user logs in, persist any session-selected hospital into user.hospital."""
    try:
        if user.hospital:
            return

        hid = None
        for key in ('current_hospital_id', 'selected_hospital_id', 'selected_hospital_code'):
            if request.session.get(key):
                hid = request.session.get(key)
                break

        if not hid:
            return

        tenant = None
        try:
            if str(hid).isdigit():
                tenant = Tenant.objects.using('default').get(id=int(hid))
            else:
                try:
                    tenant = Tenant.objects.using('default').get(subdomain=hid)
                except Tenant.DoesNotExist:
                    tenant = Tenant.objects.using('default').get(db_name=hid)
        except Exception as e:
            logger.exception('Could not resolve tenant from session key: %s', hid)
            return

        if tenant:
            try:
                user.hospital = tenant
                user.save(using='default')
                logger.info('Persisted session-selected tenant %s to user %s', tenant.id, user.username)
            except Exception:
                logger.exception('Failed to save user hospital for user %s', user.username)
    except Exception:
        logger.exception('Unexpected error in persist_session_selected_hospital')
