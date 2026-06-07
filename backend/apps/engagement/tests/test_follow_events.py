import pytest
from rest_framework.test import APIClient

from apps.accounts.tests.factories import UserFactory
from apps.engagement.models import EngagementEvent
from apps.trucks.tests.factories import TruckFactory

pytestmark = pytest.mark.django_db

FOLLOWS = "/api/v1/follows/"


def _auth(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def test_follow_via_api_logs_event():
    customer, truck = UserFactory(), TruckFactory()
    _auth(customer).post(FOLLOWS, {"truck": truck.slug}, format="json")
    assert EngagementEvent.objects.filter(
        event_type=EngagementEvent.EventType.FOLLOW, user=customer, truck=truck
    ).exists()


def test_unfollow_via_api_logs_event():
    customer, truck = UserFactory(), TruckFactory()
    client = _auth(customer)
    follow_id = client.post(FOLLOWS, {"truck": truck.slug}, format="json").json()["id"]
    client.delete(f"{FOLLOWS}{follow_id}/")
    assert EngagementEvent.objects.filter(
        event_type=EngagementEvent.EventType.UNFOLLOW, user=customer, truck=truck
    ).exists()
