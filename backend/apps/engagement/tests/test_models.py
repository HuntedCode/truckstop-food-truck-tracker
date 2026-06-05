import pytest
from django.db import IntegrityError

from apps.accounts.tests.factories import UserFactory
from apps.engagement.models import EngagementEvent
from apps.engagement.tests.factories import EngagementEventFactory, FollowFactory
from apps.trucks.tests.factories import TruckFactory

pytestmark = pytest.mark.django_db


def test_follow_is_unique_per_customer_truck():
    customer = UserFactory()
    truck = TruckFactory()
    FollowFactory(customer=customer, truck=truck)
    with pytest.raises(IntegrityError):
        FollowFactory(customer=customer, truck=truck)


def test_engagement_event_defaults_to_anonymous_empty_metadata():
    event = EngagementEventFactory()
    assert event.user is None
    assert event.metadata == {}


def test_engagement_event_records_anonymous_device_and_metadata():
    event = EngagementEventFactory(
        device_id="device-abc",
        event_type=EngagementEvent.EventType.SEARCH,
        metadata={"q": "tacos", "radius_km": 5},
    )
    assert event.device_id == "device-abc"
    assert event.metadata["q"] == "tacos"
