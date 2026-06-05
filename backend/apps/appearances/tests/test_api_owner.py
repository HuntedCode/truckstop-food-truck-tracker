from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.tests.factories import OwnerFactory, UserFactory
from apps.appearances.models import Appearance
from apps.appearances.tests.factories import AppearanceFactory
from apps.trucks.tests.factories import TruckFactory

pytestmark = pytest.mark.django_db

URL = "/api/v1/owner/appearances/"


def _payload(truck):
    now = timezone.now()
    return {
        "truck": truck.slug,
        "latitude": 30.2672,
        "longitude": -97.7431,
        "address": "123 Test St",
        "location_name": "Spot",
        "start_at": (now + timedelta(hours=1)).isoformat(),
        "end_at": (now + timedelta(hours=3)).isoformat(),
    }


def test_anonymous_cannot_create_appearance():
    resp = APIClient().post(URL, _payload(TruckFactory()), format="json")
    assert resp.status_code == 401


def test_customer_cannot_create_appearance():
    client = APIClient()
    client.force_authenticate(user=UserFactory())
    resp = client.post(URL, _payload(TruckFactory()), format="json")
    assert resp.status_code == 403


def test_owner_can_create_appearance_for_own_truck():
    owner = OwnerFactory()
    truck = TruckFactory(owner=owner)
    client = APIClient()
    client.force_authenticate(user=owner)
    resp = client.post(URL, _payload(truck), format="json")
    assert resp.status_code == 201
    appearance = Appearance.objects.get(truck=truck)
    assert abs(appearance.location.y - 30.2672) < 1e-6  # latitude
    assert abs(appearance.location.x - (-97.7431)) < 1e-6  # longitude


def test_owner_cannot_create_appearance_for_another_truck():
    owner = OwnerFactory()
    other_truck = TruckFactory()  # different owner
    client = APIClient()
    client.force_authenticate(user=owner)
    resp = client.post(URL, _payload(other_truck), format="json")
    assert resp.status_code == 400  # validate_truck rejects


def test_end_before_start_is_rejected():
    owner = OwnerFactory()
    truck = TruckFactory(owner=owner)
    client = APIClient()
    client.force_authenticate(user=owner)
    payload = _payload(truck)
    payload["end_at"] = payload["start_at"]
    resp = client.post(URL, payload, format="json")
    assert resp.status_code == 400


def test_owner_can_confirm_own_appearance():
    owner = OwnerFactory()
    appearance = AppearanceFactory(truck=TruckFactory(owner=owner))
    client = APIClient()
    client.force_authenticate(user=owner)
    resp = client.post(f"{URL}{appearance.id}/confirm/", {}, format="json")
    assert resp.status_code == 200
    appearance.refresh_from_db()
    assert appearance.last_confirmed_at is not None
    assert resp.data["is_verified_present"] is True


def test_owner_cannot_confirm_another_owners_appearance():
    appearance = AppearanceFactory()  # different owner
    client = APIClient()
    client.force_authenticate(user=OwnerFactory())
    resp = client.post(f"{URL}{appearance.id}/confirm/", {}, format="json")
    assert resp.status_code == 404
