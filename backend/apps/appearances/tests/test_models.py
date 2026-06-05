from datetime import timedelta

import pytest
from django.contrib.gis.geos import Point
from django.utils import timezone

from apps.appearances.models import Appearance
from apps.appearances.tests.factories import (
    AppearanceFactory,
    PresenceConfirmationFactory,
)
from apps.trucks.models import Truck
from apps.trucks.tests.factories import TruckFactory

pytestmark = pytest.mark.django_db


def test_is_live_within_window():
    assert AppearanceFactory().is_live() is True


def test_is_not_live_outside_window():
    past = AppearanceFactory(
        start_at=timezone.now() - timedelta(hours=5),
        end_at=timezone.now() - timedelta(hours=3),
    )
    assert past.is_live() is False


def test_owner_confirmation_updates_last_confirmed_at():
    appearance = AppearanceFactory()
    assert appearance.last_confirmed_at is None
    PresenceConfirmationFactory(appearance=appearance)
    appearance.refresh_from_db()
    assert appearance.last_confirmed_at is not None
    assert appearance.is_verified_present is True


def test_nearby_orders_by_distance_and_excludes_far():
    austin = Point(-97.7431, 30.2672, srid=4326)
    near = AppearanceFactory(location=Point(-97.7440, 30.2680, srid=4326))
    far = AppearanceFactory(location=Point(-122.4194, 37.7749, srid=4326))  # SF
    results = list(Appearance.objects.nearby(austin, radius_km=5))
    assert near in results
    assert far not in results


def test_public_excludes_unverified_truck_appearances():
    visible = AppearanceFactory()  # truck defaults active + verified
    unverified_truck = TruckFactory(
        verification_status=Truck.VerificationStatus.UNVERIFIED
    )
    hidden = AppearanceFactory(truck=unverified_truck)
    public_ids = set(Appearance.objects.public().values_list("id", flat=True))
    assert visible.id in public_ids
    assert hidden.id not in public_ids
