import pytest

from apps.accounts.models import User
from apps.accounts.tests.factories import OwnerFactory, UserFactory

pytestmark = pytest.mark.django_db


def test_create_user_defaults_to_customer():
    user = User.objects.create_user(email="c@example.com", password="pw-12345!")
    assert user.role == User.Role.CUSTOMER
    assert user.is_customer is True
    assert user.is_owner is False
    assert user.is_staff is False
    assert user.check_password("pw-12345!")


def test_create_superuser_is_staff_and_superuser():
    admin = User.objects.create_superuser(email="a@example.com", password="pw-12345!")
    assert admin.is_staff is True
    assert admin.is_superuser is True


def test_email_is_required():
    with pytest.raises(ValueError):
        User.objects.create_user(email="", password="pw-12345!")


def test_email_is_normalized():
    user = User.objects.create_user(email="Mixed@Example.COM", password="pw-12345!")
    assert user.email == "Mixed@example.com"


def test_owner_factory_sets_owner_role():
    owner = OwnerFactory()
    assert owner.is_owner is True
    assert owner.role == User.Role.OWNER


def test_str_is_email():
    user = UserFactory(email="who@example.com")
    assert str(user) == "who@example.com"


def test_create_superuser_requires_is_staff():
    with pytest.raises(ValueError):
        User.objects.create_superuser(
            email="s@example.com", password="pw-12345!", is_staff=False
        )


def test_create_superuser_requires_is_superuser():
    with pytest.raises(ValueError):
        User.objects.create_superuser(
            email="s2@example.com", password="pw-12345!", is_superuser=False
        )
