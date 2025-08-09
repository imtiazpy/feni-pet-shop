from django.http import HttpResponseForbidden
from django.core.exceptions import PermissionDenied

class RoleRequiredMixin:
    """
    Mixin to restrict view access to users with specific roles.
    Usage:
    class MyView(RoleRequiredMixin, View):
        allowed_roles = ['admin', 'inventory_manager']
    """
    allowed_roles = []

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied("Authentication required.")

        if self.allowed_roles and request.user.role not in self.allowed_roles:
            raise PermissionDenied("You do not have permission to access this view.")

        return super().dispatch(request, *args, **kwargs)
