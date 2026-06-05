import pytest
from django.contrib.gis.geos import Point
from rest_framework.test import APIClient

from apps.appearances.tests.factories import AppearanceFactory
from apps.trucks.models import Truck
from apps.trucks.tests.factories import TruckFactory

pytestmark = pytest.mark.django_db


def test_discovery_near_returns_nearby_excludes_far():
    AppearanceFactory(location=Point(-97.7440, 30.2680, srid=4326))  # near Austin
    AppearanceFactory(location=Point(-122.4194, 37.7749, srid=4326))  # San Francisco
    resp = APIClient().get("/api/v1/appearances/?lat=30.2672&lng=-97.7431&radius_km=5")
    assert resp.status_code == 200
    results = resp.data["results"]
    assert len(results) == 1
    assert results[0]["distance_km"] is not None


def test_discovery_excludes_unverified_truck_appearances():
    AppearanceFactory()  # verified, active truck
    unverified = TruckFactory(verification_status=Truck.VerificationStatus.UNVERIFIED)
    AppearanceFactory(truck=unverified)
    resp = APIClient().get("/api/v1/appearances/")
    assert resp.status_code == 200
    assert resp.data["count"] == 1


def test_near_requires_both_lat_and_lng():
    assert APIClient().get("/api/v1/appearances/?lat=30.2").status_code == 400


def test_invalid_lat_lng_is_rejected():
    assert APIClient().get("/api/v1/appearances/?lat=999&lng=-97.7").status_code == 400


def test_list_includes_coordinates_and_nested_truck():
    appearance = AppearanceFactory()
    resp = APIClient().get("/api/v1/appearances/")
    result = resp.data["results"][0]
    assert "latitude" in result and "longitude" in result
    assert result["truck"]["slug"] == appearance.truck.slug
