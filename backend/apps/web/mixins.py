from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied


class OwnerRequiredMixin(LoginRequiredMixin):
    """Require an authenticated OWNER. Anonymous -> login redirect;
    authenticated non-owner -> 403."""

    def dispatch(self, request, *args, **kwargs):
        # Anonymous users short-circuit here (is_authenticated is False) and are
        # handled by LoginRequiredMixin's redirect. Keep this order so we never
        # read is_owner on an AnonymousUser.
        if request.user.is_authenticated and not request.user.is_owner:
            raise PermissionDenied("An owner account is required.")
        return super().dispatch(request, *args, **kwargs)


class CustomerRequiredMixin(LoginRequiredMixin):
    """Require an authenticated CUSTOMER. Anonymous -> login redirect (so they
    can sign in and come back); authenticated owner -> 403 (owners can't follow
    trucks). Same anonymous-first ordering as OwnerRequiredMixin."""

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.is_customer:
            raise PermissionDenied("A customer account is required.")
        return super().dispatch(request, *args, **kwargs)
