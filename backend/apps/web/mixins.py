from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied


class OwnerRequiredMixin(LoginRequiredMixin):
    """Require an authenticated OWNER. Anonymous -> login redirect;
    authenticated non-owner -> 403."""

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.is_owner:
            raise PermissionDenied("An owner account is required.")
        return super().dispatch(request, *args, **kwargs)
