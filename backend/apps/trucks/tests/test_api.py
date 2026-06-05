import pytest
from rest_framework.test import APIClient

from apps.trucks.models import Truck
from apps.trucks.tests.factories import CuisineFactory, TruckFactory

pytestmark = pytest.mark.django_db


def test_anonymous_lists_only_verified_active_trucks():
    visible = TruckFactory(name="Visible")  # active + verified (factory default)
    draft = TruckFactory(name="Draft", status=Truck.Status.DRAFT)
    unverified = TruckFactory(
        name="Unverified",
        verification_status=Truck.VerificationStatus.UNVERIFIED,
    )
    resp = APIClient().get("/api/v1/trucks/")
    assert resp.status_code == 200
    slugs = {t["slug"] for t in resp.data["results"]}
    assert visible.slug in slugs
    assert draft.slug not in slugs
    assert unverified.slug not in slugs


def test_truck_detail_by_slug():
    truck = TruckFactory(name="Detail Truck")
    resp = APIClient().get(f"/api/v1/trucks/{truck.slug}/")
    assert resp.status_code == 200
    assert resp.data["name"] == "Detail Truck"


def test_cuisine_filter():
    korean = CuisineFactory(name="Korean")
    mexican = CuisineFactory(name="Mexican")
    k_truck = TruckFactory(primary_cuisine=korean)
    m_truck = TruckFactory(primary_cuisine=mexican)
    resp = APIClient().get(f"/api/v1/trucks/?cuisine={korean.slug}")
    slugs = {t["slug"] for t in resp.data["results"]}
    assert k_truck.slug in slugs
    assert m_truck.slug not in slugs


def test_cuisine_list_is_unpaginated():
    CuisineFactory(name="Tacos")
    CuisineFactory(name="BBQ")
    resp = APIClient().get("/api/v1/cuisines/")
    assert resp.status_code == 200
    assert isinstance(resp.data, list)  # pagination_class = None


def test_draft_or_unverified_truck_detail_returns_404():
    draft = TruckFactory(status=Truck.Status.DRAFT)
    unverified = TruckFactory(verification_status=Truck.VerificationStatus.UNVERIFIED)
    client = APIClient()
    assert client.get(f"/api/v1/trucks/{draft.slug}/").status_code == 404
    assert client.get(f"/api/v1/trucks/{unverified.slug}/").status_code == 404


def test_truck_exposes_is_verified_not_status():
    truck = TruckFactory()
    resp = APIClient().get(f"/api/v1/trucks/{truck.slug}/")
    assert resp.data["is_verified"] is True
    assert "verification_status" not in resp.data


def test_truck_list_uses_paginated_envelope():
    TruckFactory()
    resp = APIClient().get("/api/v1/trucks/")
    for key in ("count", "next", "previous", "results"):
        assert key in resp.data
