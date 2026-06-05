import pytest
from django.db import IntegrityError

from apps.notifications.tests.factories import (
    NotificationPreferenceFactory,
    PushTokenFactory,
)

pytestmark = pytest.mark.django_db


def test_notification_preference_defaults():
    pref = NotificationPreferenceFactory()
    assert pref.push_enabled is True
    assert pref.email_marketing_opt_in is False


def test_push_token_is_unique():
    PushTokenFactory(token="dupe-token")
    with pytest.raises(IntegrityError):
        PushTokenFactory(token="dupe-token")
