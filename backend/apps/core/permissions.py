from rest_framework.permissions import BasePermission


class IsOwnerRole(BasePermission):
    """Authenticated user with the OWNER role."""

    message = "An owner account is required."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_owner)


class IsCustomerRole(BasePermission):
    """Authenticated user with the CUSTOMER role."""

    message = "A customer account is required."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_customer)
