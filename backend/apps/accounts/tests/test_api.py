import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.accounts.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


def test_register_creates_customer():
    client = APIClient()
    resp = client.post(
        "/api/v1/auth/register/",
        {
            "email": "new@example.com",
            "password": "s3curePass!",
            "role": "CUSTOMER",
            "display_name": "New",
        },
        format="json",
    )
    assert resp.status_code == 201
    user = User.objects.get(email="new@example.com")
    assert user.role == User.Role.CUSTOMER
    assert user.check_password("s3curePass!")
    assert "password" not in resp.data


def test_register_rejects_weak_password():
    client = APIClient()
    resp = client.post(
        "/api/v1/auth/register/",
        {"email": "weak@example.com", "password": "123", "role": "CUSTOMER"},
        format="json",
    )
    assert resp.status_code == 400


def test_register_requires_role():
    client = APIClient()
    resp = client.post(
        "/api/v1/auth/register/",
        {"email": "norole@example.com", "password": "s3curePass!"},
        format="json",
    )
    assert resp.status_code == 400


def test_me_requires_auth():
    assert APIClient().get("/api/v1/auth/me/").status_code == 401


def test_me_returns_current_user():
    user = UserFactory(email="me@example.com")
    client = APIClient()
    client.force_authenticate(user=user)
    resp = client.get("/api/v1/auth/me/")
    assert resp.status_code == 200
    assert resp.data["email"] == "me@example.com"
