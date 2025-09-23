from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from functools import wraps
from django.core.exceptions import FieldDoesNotExist


@method_decorator(login_required, name='dispatch')
class SafeMixin:
    """Mixin for ZAIN HMS unified system.

    - Enforces login and optional role checks via `required_roles`.
    """

    required_roles = []

    def dispatch(self, request, *args, **kwargs):
        # Role-based access enforcement
        if hasattr(self, 'required_roles') and self.required_roles:
            if not request.user.is_authenticated:
                return redirect('accounts:login')

            required_roles_upper = [role.upper() for role in self.required_roles]
            user_role_upper = request.user.role.upper() if getattr(request.user, 'role', None) else ''

            if user_role_upper != 'SUPERADMIN' and user_role_upper not in required_roles_upper:
                raise PermissionDenied(f"Access denied. Required roles: {', '.join(required_roles_upper)}")

        return super().dispatch(request, *args, **kwargs)


class UnifiedSystemMixin:
    """Mixin for ZAIN HMS unified system.

    Keeps behaviour simple for single-hospital deployments.
    """

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
