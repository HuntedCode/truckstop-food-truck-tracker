import pytest
from django.urls import reverse

from apps.accounts.models import User
from apps.accounts.tests.factories import OwnerFactory, UserFactory

pytestmark = pytest.mark.django_db

_VALID = {
    "email": "casey@example.com",
    "display_name": "Casey",
    "password1": "s3curePass!",
    "password2": "s3curePass!",
}


# --- Customer sign-up ------------------------------------------------------


def test_signup_creates_customer_and_logs_in(client):
    resp = client.post(reverse("signup"), _VALID)
    assert resp.status_code == 302
    assert resp.url == reverse("home")
    user = User.objects.get(email="casey@example.com")
    assert user.is_customer  # role stamped server-side, not from POST
    # The new customer is signed in and can reach a customer-only page.
    assert client.get(reverse("following")).status_code == 200


def test_signup_respects_safe_next(client):
    resp = client.post(reverse("signup") + "?next=/t/taco-loco/", _VALID)
    assert resp.url == "/t/taco-loco/"


def test_signup_ignores_offsite_next(client):
    resp = client.post(reverse("signup") + "?next=http://evil.example.com/x", _VALID)
    assert resp.url == reverse("home")  # open-redirect guard


def test_signup_redirects_authenticated_user(client):
    client.force_login(UserFactory())
    assert client.get(reverse("signup")).status_code == 302


def test_signup_rejects_duplicate_email(client):
    UserFactory(email="casey@example.com")
    resp = client.post(reverse("signup"), _VALID)
    assert resp.status_code == 200  # re-rendered with error
    assert User.objects.filter(email="casey@example.com").count() == 1


# --- Role-aware login ------------------------------------------------------


def test_login_routes_customer_to_home(client):
    customer = UserFactory()  # factory password: password123!
    resp = client.post(
        reverse("login"), {"username": customer.email, "password": "password123!"}
    )
    assert resp.status_code == 302
    assert resp.url == reverse("home")


def test_login_routes_owner_to_dashboard(client):
    owner = OwnerFactory()
    resp = client.post(
        reverse("login"), {"username": owner.email, "password": "password123!"}
    )
    assert resp.status_code == 302
    assert resp.url == reverse("dashboard")


def test_login_respects_next(client):
    customer = UserFactory()
    resp = client.post(
        reverse("login"),
        {"username": customer.email, "password": "password123!", "next": "/t/x/"},
    )
    assert resp.url == "/t/x/"


def test_login_ignores_offsite_next(client):
    customer = UserFactory()
    resp = client.post(
        reverse("login"),
        {
            "username": customer.email,
            "password": "password123!",
            "next": "http://evil.example.com/x",
        },
    )
    assert resp.url == reverse(
        "home"
    )  # open-redirect guard, falls back to role default
