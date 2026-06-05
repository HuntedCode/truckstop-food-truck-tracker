import pytest
from rest_framework.test import APIClient

from apps.accounts.tests.factories import UserFactory
from apps.notifications.models import NotificationPreference, PushToken

pytestmark = pytest.mark.django_db

PREFS = "/api/v1/notification-preference/"
TOKENS = "/api/v1/push-tokens/"


def _auth(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


# --- notification preferences ---


def test_prefs_requires_auth():
    assert APIClient().get(PREFS).status_code == 401


def test_get_creates_and_returns_defaults():
    user = UserFactory()
    resp = _auth(user).get(PREFS)
    assert resp.status_code == 200
    assert resp.data["push_enabled"] is True
    assert resp.data["email_marketing_opt_in"] is False
    assert NotificationPreference.objects.filter(user=user).exists()


def test_patch_updates_prefs():
    user = UserFactory()
    resp = _auth(user).patch(PREFS, {"push_enabled": False}, format="json")
    assert resp.status_code == 200
    assert resp.data["push_enabled"] is False


# --- push tokens ---


def test_register_push_token():
    user = UserFactory()
    resp = _auth(user).post(
        TOKENS, {"token": "ExponentPushToken[abc]", "platform": "IOS"}, format="json"
    )
    assert resp.status_code == 201
    assert PushToken.objects.filter(token="ExponentPushToken[abc]", user=user).exists()


def test_register_existing_token_upserts_to_current_user():
    first, second = UserFactory(), UserFactory()
    _auth(first).post(TOKENS, {"token": "tok", "platform": "IOS"}, format="json")
    resp = _auth(second).post(
        TOKENS, {"token": "tok", "platform": "ANDROID"}, format="json"
    )
    assert resp.status_code == 200
    token = PushToken.objects.get(token="tok")
    assert token.user == second
    assert token.platform == "ANDROID"


def test_list_only_own_push_tokens():
    user = UserFactory()
    PushToken.objects.create(user=user, token="a", platform="IOS")
    PushToken.objects.create(user=UserFactory(), token="b", platform="IOS")
    resp = _auth(user).get(TOKENS)
    assert resp.data["count"] == 1


def test_delete_push_token():
    user = UserFactory()
    token = PushToken.objects.create(user=user, token="a", platform="IOS")
    resp = _auth(user).delete(f"{TOKENS}{token.id}/")
    assert resp.status_code == 204
    assert not PushToken.objects.filter(id=token.id).exists()


def test_push_tokens_require_auth():
    assert APIClient().get(TOKENS).status_code == 401
