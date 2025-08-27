from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps


class TenantSafeMixin:
    """Provide tenant-aware helpers that work with per-DB routing or no tenant FK.

    - filter_by_tenant(queryset): If model has 'tenant' field, filter by request.tenant; otherwise passthrough.
    - get_tenant_safe_queryset(Model): Same as above but starts from Model.objects.
    - get_current_tenant(): Returns a lightweight indicator based on session or request attributes.
    """

    def get_current_tenant(self):
        # Prefer a session marker code; otherwise any request attribute set by middleware
        if hasattr(self, 'request'):
            code = self.request.session.get('selected_hospital_code')
            if code:
                return code
            return getattr(self.request, 'tenant', None)
        return None

    def _model_has_tenant_field(self, model):
        try:
            model._meta.get_field('tenant')
            return True
        except Exception:
            return False

    def filter_by_tenant(self, queryset):
        model = queryset.model
        if self._model_has_tenant_field(model):
            tenant = getattr(getattr(self, 'request', None), 'tenant', None)
            return queryset.filter(tenant=tenant) if tenant else queryset.none()
        return queryset

    def get_tenant_safe_queryset(self, Model):
        if self._model_has_tenant_field(Model):
            tenant = getattr(getattr(self, 'request', None), 'tenant', None)
            return Model.objects.filter(tenant=tenant) if tenant else Model.objects.none()
        return Model.objects.all()


class RequireHospitalSelectionMixin:
    """Mixin to enforce explicit hospital selection via session before proceeding.
    
    This applies to ALL users including SUPERADMIN - no one can create records
    or access settings without explicitly selecting a hospital first.
    """

    selection_message = 'Please select a hospital first to proceed.'

    def dispatch(self, request, *args, **kwargs):
        # Check if hospital is selected in session
        selected_hospital_code = request.session.get('selected_hospital_code')
        
        if not selected_hospital_code:
            # Log the attempt for security monitoring
            user_info = f"User: {request.user.username} (Role: {getattr(request.user, 'role', 'Unknown')})"
            messages.warning(request, f'{self.selection_message} {user_info}')
            # Remember where to go back after selecting hospital
            try:
                request.session['post_select_redirect'] = request.get_full_path()
            except Exception:
                request.session['post_select_redirect'] = '/'
            return redirect('tenants:hospital_selection')
            
        return super().dispatch(request, *args, **kwargs)


def require_hospital_selection(view_func):
    """Decorator to enforce hospital selection for function-based views.

    Redirects to the hospital selection page if no selected_hospital marker is present
    in the session. Applies to UI add/create endpoints so users must choose a hospital first.
    """
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not (request.session.get('selected_hospital_code') or request.session.get('selected_hospital_id')):
            messages.info(request, 'Please select a hospital first to proceed.')
            return redirect('tenants:hospital_selection')
        return view_func(request, *args, **kwargs)
    return _wrapped
from django.core.exceptions import FieldDoesNotExist


class TenantSafeMixin:
    """Tenant-aware helpers compatible with per-DB routing.

    If a model doesn't have a 'tenant' field, we return unfiltered querysets and
    rely on the database router to isolate data per hospital.
    """

    def get_current_tenant(self):
        # Prefer request.tenant if set upstream; else None
        return getattr(getattr(self, 'request', None), 'tenant', None)

    def _model_has_tenant_field(self, model):
        try:
            model._meta.get_field('tenant')
            return True
        except Exception:
            return False

    def filter_by_tenant(self, queryset):
        model = queryset.model
        if self._model_has_tenant_field(model):
            tenant = self.get_current_tenant()
            return queryset.filter(tenant=tenant) if tenant else queryset.none()
        return queryset

    def get_tenant_safe_queryset(self, Model):
        if self._model_has_tenant_field(Model):
            tenant = self.get_current_tenant()
            return Model.objects.filter(tenant=tenant) if tenant else Model.objects.none()
        return Model.objects.all()
