from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin, TimeStampedModel):
    """Email-login user with a foundational owner/customer role split.

    Roles are strict: an account is either an OWNER or a CUSTOMER, never both
    (see docs/architecture/decisions/0002-strict-role-separation.md).
    """

    class Role(models.TextChoices):
        OWNER = "OWNER", "Owner"
        CUSTOMER = "CUSTOMER", "Customer"

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=8, choices=Role.choices)
    display_name = models.CharField(max_length=120, blank=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []  # createsuperuser prompts for email + password.

    class Meta:
        db_table = "accounts_user"

    def __str__(self):
        return self.email

    @property
    def is_owner(self):
        return self.role == self.Role.OWNER

    @property
    def is_customer(self):
        return self.role == self.Role.CUSTOMER
