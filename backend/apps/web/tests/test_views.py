import pytest
from django.urls import reverse

from apps.accounts.models import User
from apps.accounts.tests.factories import OwnerFactory, UserFactory

pytestmark = pytest.mark.django_db


def test_register_creates_owner_and_logs_in(client):
    resp = client.post(
        reverse("register"),
        {
            "email": "owner@example.com",
            "display_name": "Taco Owner",
            "password1": "s3curePass!",
            "password2": "s3curePass!",
        },
    )
    assert resp.status_code == 302
    user = User.objects.get(email="owner@example.com")
    assert user.is_owner
    # The new owner is logged in and can reach the dashboard.
    assert client.get(reverse("dashboard")).status_code == 200


def test_register_password_mismatch_does_not_create_user(client):
    resp = client.post(
        reverse("register"),
        {
            "email": "x@example.com",
            "password1": "s3curePass!",
            "password2": "nope",
        },
    )
    assert resp.status_code == 200  # re-rendered with errors
    assert not User.objects.filter(email="x@example.com").exists()


def test_dashboard_requires_login(client):
    resp = client.get(reverse("dashboard"))
    assert resp.status_code == 302
    assert reverse("login") in resp.url


def test_dashboard_forbidden_for_customer(client):
    client.force_login(UserFactory())  # CUSTOMER
    assert client.get(reverse("dashboard")).status_code == 403


def test_owner_sees_dashboard(client):
    client.force_login(OwnerFactory())
    resp = client.get(reverse("dashboard"))
    assert resp.status_code == 200
    assert b"Your trucks" in resp.content
