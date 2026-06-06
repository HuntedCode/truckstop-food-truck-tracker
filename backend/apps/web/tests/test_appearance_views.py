from unittest.mock import patch
from zoneinfo import ZoneInfo

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.accounts.tests.factories import OwnerFactory, UserFactory
from apps.appearances.models import Appearance
from apps.appearances.tests.factories import AppearanceFactory
from apps.core.geocoding import GeocodeResult, GeocodingError
from apps.trucks.tests.factories import TruckFactory

pytestmark = pytest.mark.django_db

# Austin, TX, returned by the mocked geocoder (lat, lng).
_GEO = GeocodeResult(30.2672, -97.7431, "100 Congress Ave, Austin, TX")

_VALID_POST = {
    "address": "100 Congress Ave, Austin",
    "location_name": "Downtown",
    "date": "2026-06-10",
    "start_time": "11:00",
    "end_time": "14:00",
}


# --- Manage page ------------------------------------------------------------


def test_manage_requires_login(client):
    truck = TruckFactory()
    resp = client.get(reverse("truck-manage", args=[truck.slug]))
    assert resp.status_code == 302
    assert reverse("login") in resp.url


def test_manage_forbidden_for_customer(client):
    truck = TruckFactory()
    client.force_login(UserFactory())
    assert client.get(reverse("truck-manage", args=[truck.slug])).status_code == 403


def test_owner_sees_manage_page_with_appearances(client):
    owner = OwnerFactory()
    truck = TruckFactory(owner=owner, name="Taco Loco")
    AppearanceFactory(truck=truck, location_name="Mueller Park")
    client.force_login(owner)
    resp = client.get(reverse("truck-manage", args=[truck.slug]))
    assert resp.status_code == 200
    assert b"Taco Loco" in resp.content
    assert b"Mueller Park" in resp.content


def test_manage_another_owners_truck_404(client):
    other = TruckFactory()
    client.force_login(OwnerFactory())
    assert client.get(reverse("truck-manage", args=[other.slug])).status_code == 404


# --- Create -----------------------------------------------------------------


def test_create_requires_login(client):
    truck = TruckFactory()
    resp = client.get(reverse("appearance-create", args=[truck.slug]))
    assert resp.status_code == 302
    assert reverse("login") in resp.url


def test_create_forbidden_for_customer(client):
    truck = TruckFactory()
    client.force_login(UserFactory())
    assert (
        client.get(reverse("appearance-create", args=[truck.slug])).status_code == 403
    )


def test_owner_opens_create_form(client):
    owner = OwnerFactory()
    truck = TruckFactory(owner=owner)
    client.force_login(owner)
    resp = client.get(reverse("appearance-create", args=[truck.slug]))
    assert resp.status_code == 200
    assert b"Post an appearance" in resp.content


@patch("apps.web.forms.geocode", return_value=_GEO)
def test_owner_posts_appearance(mock_geocode, client):
    owner = OwnerFactory()
    truck = TruckFactory(owner=owner, timezone="America/Chicago")
    client.force_login(owner)
    resp = client.post(reverse("appearance-create", args=[truck.slug]), _VALID_POST)
    assert resp.status_code == 302
    appearance = truck.appearances.get()
    assert appearance.location_name == "Downtown"
    assert appearance.coordinates_confirmed is False
    # 11:00-14:00 entered in Central, stored as UTC, reads back as 11:00 Central.
    local_start = timezone.localtime(appearance.start_at, ZoneInfo("America/Chicago"))
    assert (local_start.hour, local_start.minute) == (11, 0)
    # PostGIS stores x=lng, y=lat.
    assert appearance.location.x == pytest.approx(-97.7431)
    assert appearance.location.y == pytest.approx(30.2672)


@patch("apps.web.forms.geocode", return_value=None)
def test_create_address_not_found_shows_error(mock_geocode, client):
    owner = OwnerFactory()
    truck = TruckFactory(owner=owner)
    client.force_login(owner)
    resp = client.post(reverse("appearance-create", args=[truck.slug]), _VALID_POST)
    assert resp.status_code == 200  # re-rendered with a field error
    assert truck.appearances.count() == 0


@patch("apps.web.forms.geocode", side_effect=GeocodingError("service down"))
def test_create_geocode_unavailable_shows_error(mock_geocode, client):
    owner = OwnerFactory()
    truck = TruckFactory(owner=owner)
    client.force_login(owner)
    resp = client.post(reverse("appearance-create", args=[truck.slug]), _VALID_POST)
    assert resp.status_code == 200
    assert truck.appearances.count() == 0


@patch("apps.web.forms.geocode", return_value=_GEO)
def test_create_rejects_end_before_start(mock_geocode, client):
    owner = OwnerFactory()
    truck = TruckFactory(owner=owner)
    client.force_login(owner)
    resp = client.post(
        reverse("appearance-create", args=[truck.slug]),
        {**_VALID_POST, "start_time": "14:00", "end_time": "11:00"},
    )
    assert resp.status_code == 200
    assert truck.appearances.count() == 0


def test_create_on_another_owners_truck_404(client):
    other = TruckFactory()
    client.force_login(OwnerFactory())
    assert (
        client.get(reverse("appearance-create", args=[other.slug])).status_code == 404
    )


# --- Edit / cancel ----------------------------------------------------------


@patch("apps.web.forms.geocode", return_value=_GEO)
def test_owner_edits_appearance(mock_geocode, client):
    owner = OwnerFactory()
    truck = TruckFactory(owner=owner, timezone="America/Chicago")
    appearance = AppearanceFactory(truck=truck)
    client.force_login(owner)
    resp = client.post(
        reverse("appearance-edit", args=[appearance.pk]),
        {**_VALID_POST, "location_name": "New Spot"},
    )
    assert resp.status_code == 302
    appearance.refresh_from_db()
    assert appearance.location_name == "New Spot"


def test_edit_another_owners_appearance_404(client):
    appearance = AppearanceFactory()  # different owner
    client.force_login(OwnerFactory())
    assert (
        client.get(reverse("appearance-edit", args=[appearance.pk])).status_code == 404
    )


def test_owner_cancels_appearance(client):
    owner = OwnerFactory()
    truck = TruckFactory(owner=owner)
    appearance = AppearanceFactory(truck=truck)
    client.force_login(owner)
    resp = client.post(reverse("appearance-cancel", args=[appearance.pk]))
    assert resp.status_code == 302
    appearance.refresh_from_db()
    assert appearance.status == Appearance.Status.CANCELED


def test_cancel_requires_post(client):
    owner = OwnerFactory()
    truck = TruckFactory(owner=owner)
    appearance = AppearanceFactory(truck=truck)
    client.force_login(owner)
    assert (
        client.get(reverse("appearance-cancel", args=[appearance.pk])).status_code
        == 405
    )


def test_cancel_another_owners_appearance_404(client):
    appearance = AppearanceFactory()
    client.force_login(OwnerFactory())
    assert (
        client.post(reverse("appearance-cancel", args=[appearance.pk])).status_code
        == 404
    )


# --- "I'm here now" confirm -------------------------------------------------


def test_htmx_confirm_returns_updated_card(client):
    owner = OwnerFactory()
    truck = TruckFactory(owner=owner)
    appearance = AppearanceFactory(truck=truck)  # live by default
    client.force_login(owner)
    resp = client.post(
        reverse("appearance-confirm", args=[appearance.pk]), HTTP_HX_REQUEST="true"
    )
    assert resp.status_code == 200
    assert b"Live since" in resp.content  # the swapped-in confirmed state
    appearance.refresh_from_db()
    assert appearance.is_verified_present is True


def test_plain_confirm_redirects_to_manage(client):
    owner = OwnerFactory()
    truck = TruckFactory(owner=owner)
    appearance = AppearanceFactory(truck=truck)
    client.force_login(owner)
    resp = client.post(reverse("appearance-confirm", args=[appearance.pk]))
    assert resp.status_code == 302
    assert resp.url == reverse("truck-manage", args=[truck.slug])
    appearance.refresh_from_db()
    assert appearance.is_verified_present is True


def test_confirm_canceled_appearance_is_rejected(client):
    owner = OwnerFactory()
    truck = TruckFactory(owner=owner)
    appearance = AppearanceFactory(truck=truck, status=Appearance.Status.CANCELED)
    client.force_login(owner)
    resp = client.post(reverse("appearance-confirm", args=[appearance.pk]))
    assert resp.status_code == 302  # redirected with an error message
    appearance.refresh_from_db()
    assert appearance.last_confirmed_at is None


def test_confirm_requires_post(client):
    owner = OwnerFactory()
    truck = TruckFactory(owner=owner)
    appearance = AppearanceFactory(truck=truck)
    client.force_login(owner)
    assert (
        client.get(reverse("appearance-confirm", args=[appearance.pk])).status_code
        == 405
    )


def test_confirm_forbidden_for_customer(client):
    appearance = AppearanceFactory()
    client.force_login(UserFactory())
    assert (
        client.post(reverse("appearance-confirm", args=[appearance.pk])).status_code
        == 403
    )


def test_confirm_another_owners_appearance_404(client):
    appearance = AppearanceFactory()
    client.force_login(OwnerFactory())
    assert (
        client.post(reverse("appearance-confirm", args=[appearance.pk])).status_code
        == 404
    )
