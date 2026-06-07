from datetime import timedelta
from unittest.mock import patch

import pytest
from django.contrib.gis.geos import Point
from django.core.cache import cache
from django.urls import reverse
from django.utils import timezone

from apps.appearances.models import Appearance
from apps.appearances.tests.factories import AppearanceFactory
from apps.core.geocoding import GeocodeResult, GeocodingError
from apps.trucks.models import Truck
from apps.trucks.tests.factories import TruckFactory
from apps.web.views import AddressSearchView

pytestmark = pytest.mark.django_db

# Far from the Austin default discovery area, near the factory's default point.
MIAMI = Point(-80.1918, 25.7617, srid=4326)


# --- DiscoveryView (home) --------------------------------------------------


def test_home_is_public(client):
    # Anonymous visitors get the discovery page, never a login redirect.
    resp = client.get(reverse("home"))
    assert resp.status_code == 200
    assert b"Find food trucks near you" in resp.content


def test_default_location_shows_nearby_live_truck(client):
    AppearanceFactory(truck__name="Taco Loco")  # live, at the default point
    resp = client.get(reverse("home"))
    assert b"Taco Loco" in resp.content
    assert b"Here now" in resp.content


def test_live_listed_before_soon(client):
    AppearanceFactory(truck__name="Live Truck")  # factory default: live now
    AppearanceFactory(
        truck__name="Soon Truck",
        start_at=timezone.now() + timedelta(hours=2),
        end_at=timezone.now() + timedelta(hours=4),
    )
    content = client.get(reverse("home")).content.decode()
    assert "Live Truck" in content and "Soon Truck" in content
    assert content.index("Here now") < content.index("Coming soon")
    assert content.index("Live Truck") < content.index("Soon Truck")


def test_truck_beyond_radius_excluded(client):
    AppearanceFactory(truck__name="Faraway", location=MIAMI)
    resp = client.get(reverse("home"))
    assert b"Faraway" not in resp.content
    assert b"No trucks here yet" in resp.content


def test_unverified_truck_hidden(client):
    AppearanceFactory(
        truck__name="Unverified",
        truck__verification_status=Truck.VerificationStatus.UNVERIFIED,
    )
    assert b"Unverified" not in client.get(reverse("home")).content


def test_paused_truck_hidden(client):
    AppearanceFactory(truck__name="Paused", truck__status=Truck.Status.PAUSED)
    assert b"Paused" not in client.get(reverse("home")).content


def test_canceled_appearance_hidden(client):
    AppearanceFactory(truck__name="Gone Co", status=Appearance.Status.CANCELED)
    assert b"Gone Co" not in client.get(reverse("home")).content


def test_picked_coordinates_filter_and_persist(client):
    AppearanceFactory(truck__name="Beach Truck", location=MIAMI)
    # The picked coordinates surface the Miami truck (not in the default area).
    resp = client.get(
        reverse("home"), {"lat": "25.7617", "lng": "-80.1918", "label": "Miami, FL"}
    )
    assert b"Beach Truck" in resp.content
    assert b"Miami, FL" in resp.content
    # The choice persists in the session: a later visit with no params keeps it.
    resp2 = client.get(reverse("home"))
    assert b"Beach Truck" in resp2.content


def test_bad_coordinates_fall_back_to_default(client):
    AppearanceFactory(truck__name="Default Truck")  # at the default point
    resp = client.get(reverse("home"), {"lat": "not", "lng": "anumber"})
    assert resp.status_code == 200
    assert b"Default Truck" in resp.content


@patch("apps.web.views.geocode")
def test_typed_address_is_geocoded(mock_geocode, client):
    mock_geocode.return_value = GeocodeResult(25.7617, -80.1918, "Miami, FL")
    AppearanceFactory(truck__name="Beach Truck", location=MIAMI)
    resp = client.get(reverse("home"), {"address": "Miami"})
    assert b"Beach Truck" in resp.content
    mock_geocode.assert_called_once()


@patch("apps.web.views.geocode", side_effect=GeocodingError("down"))
def test_typed_address_geocode_failure_falls_back(mock_geocode, client):
    AppearanceFactory(truck__name="Default Truck")  # at the default point
    resp = client.get(reverse("home"), {"address": "somewhere"})
    assert resp.status_code == 200
    assert b"Default Truck" in resp.content  # fell back to the default area


# --- TruckDetailView -------------------------------------------------------


def test_truck_detail_public(client):
    appearance = AppearanceFactory(truck__name="Taco Loco")
    resp = client.get(reverse("truck-detail", args=[appearance.truck.slug]))
    assert resp.status_code == 200
    assert b"Taco Loco" in resp.content
    assert b"Where to find" in resp.content
    assert b"Test Spot" in resp.content  # the appearance location_name


def test_truck_detail_404_for_draft(client):
    truck = TruckFactory(
        status=Truck.Status.DRAFT,
        verification_status=Truck.VerificationStatus.UNVERIFIED,
    )
    assert client.get(reverse("truck-detail", args=[truck.slug])).status_code == 404


def test_truck_detail_404_for_paused(client):
    truck = TruckFactory(status=Truck.Status.PAUSED)
    assert client.get(reverse("truck-detail", args=[truck.slug])).status_code == 404


def test_truck_detail_no_upcoming_message(client):
    truck = TruckFactory(name="Quiet Truck")  # active + verified, no appearances
    resp = client.get(reverse("truck-detail", args=[truck.slug]))
    assert resp.status_code == 200
    assert b"No upcoming stops posted yet" in resp.content


# --- AddressSearchView (now public) ----------------------------------------


@patch("apps.web.views.geocode_search")
def test_address_search_anonymous_allowed(mock_search, client):
    mock_search.return_value = [
        GeocodeResult(30.2672, -97.7431, "Congress Ave, Austin")
    ]
    resp = client.get(reverse("address-search"), {"address": "Congress Ave"})
    assert resp.status_code == 200
    assert b"Congress Ave, Austin" in resp.content


@patch("apps.web.views.geocode_search", side_effect=GeocodingError("down"))
def test_address_search_handles_service_error(mock_search, client):
    resp = client.get(reverse("address-search"), {"address": "anything"})
    assert resp.status_code == 200
    assert b"unavailable" in resp.content


def test_address_search_empty_query_is_ok(client):
    resp = client.get(reverse("address-search"))
    assert resp.status_code == 200


@patch("apps.web.views.geocode_search", return_value=[])
def test_address_search_throttled_after_limit(mock_search, client):
    cache.clear()  # isolate the fixed-window counter from other tests
    for _ in range(AddressSearchView.THROTTLE_LIMIT):
        assert (
            client.get(reverse("address-search"), {"address": "x"}).status_code == 200
        )
    resp = client.get(reverse("address-search"), {"address": "x"})
    assert b"Too many searches" in resp.content
