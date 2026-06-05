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


def test_register_redirects_authenticated_user_to_dashboard(client):
    client.force_login(OwnerFactory())
    resp = client.get(reverse("register"))
    assert resp.status_code == 302
    assert resp.url == reverse("dashboard")


def test_owner_can_log_in(client):
    User.objects.create_user(
        email="o@example.com", password="s3curePass!", role=User.Role.OWNER
    )
    resp = client.post(
        reverse("login"), {"username": "o@example.com", "password": "s3curePass!"}
    )
    assert resp.status_code == 302
    assert client.get(reverse("dashboard")).status_code == 200


def test_login_is_case_insensitive(client):
    client.post(
        reverse("register"),
        {
            "email": "Mixed@Example.com",
            "password1": "s3curePass!",
            "password2": "s3curePass!",
        },
    )
    client.logout()
    resp = client.post(
        reverse("login"), {"username": "MIXED@example.COM", "password": "s3curePass!"}
    )
    assert resp.status_code == 302
    assert client.get(reverse("dashboard")).status_code == 200


def test_logout_ends_session(client):
    client.force_login(OwnerFactory())
    assert client.get(reverse("dashboard")).status_code == 200
    resp = client.post(reverse("logout"))
    assert resp.status_code == 302
    assert client.get(reverse("dashboard")).status_code == 302  # back to login


def test_home_redirects_to_dashboard(client):
    resp = client.get(reverse("home"))
    assert resp.status_code == 302
    assert resp.url == reverse("dashboard")


def test_login_redirects_authenticated_user(client):
    client.force_login(OwnerFactory())
    resp = client.get(reverse("login"))
    assert resp.status_code == 302
    assert resp.url == reverse("dashboard")


def test_duplicate_email_registration_is_rejected(client):
    OwnerFactory(email="dupe@example.com")
    resp = client.post(
        reverse("register"),
        {
            "email": "Dupe@Example.com",  # different casing
            "password1": "s3curePass!",
            "password2": "s3curePass!",
        },
    )
    assert resp.status_code == 200
    assert User.objects.filter(email__iexact="dupe@example.com").count() == 1


def test_weak_password_is_rejected(client):
    resp = client.post(
        reverse("register"),
        {"email": "w@example.com", "password1": "12345678", "password2": "12345678"},
    )
    assert resp.status_code == 200
    assert not User.objects.filter(email="w@example.com").exists()
