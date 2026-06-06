import json
import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from apps.core.geocoding import (
    GeocodeResult,
    GeocodingClient,
    GeocodingError,
    NominatimGeocoder,
)


class _FakeGeocoder:
    """Returns/raises a scripted sequence of outcomes, one per geocode_once."""

    def __init__(self, outcomes):
        self._outcomes = list(outcomes)
        self.calls = 0

    def geocode_once(self, address):
        self.calls += 1
        outcome = self._outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


# --- GeocodingClient: retry / backoff / degradation (no HTTP) ---------------


def test_returns_result_on_success():
    result = GeocodeResult(40.0, -74.0, "Somewhere")
    client = GeocodingClient(
        geocoder=_FakeGeocoder([result]), max_retries=2, sleep=lambda s: None
    )
    assert client.geocode("123 Main St") == result


def test_blank_address_returns_none_without_calling():
    geo = _FakeGeocoder([GeocodeResult(1, 1, "x")])
    client = GeocodingClient(geocoder=geo, sleep=lambda s: None)
    assert client.geocode("   ") is None
    assert geo.calls == 0


def test_no_match_returns_none():
    client = GeocodingClient(geocoder=_FakeGeocoder([None]), sleep=lambda s: None)
    assert client.geocode("nowhere") is None


def test_retries_then_succeeds_with_exponential_backoff():
    result = GeocodeResult(1.0, 2.0, "ok")
    geo = _FakeGeocoder([GeocodingError("boom"), GeocodingError("boom"), result])
    sleeps = []
    client = GeocodingClient(
        geocoder=geo, max_retries=2, backoff=0.5, sleep=sleeps.append
    )
    assert client.geocode("retry me") == result
    assert geo.calls == 3
    assert sleeps == [0.5, 1.0]  # 0.5 * 2**0, then 0.5 * 2**1


def test_raises_after_exhausting_retries():
    geo = _FakeGeocoder([GeocodingError("down")] * 3)
    sleeps = []
    client = GeocodingClient(
        geocoder=geo, max_retries=2, backoff=0.5, sleep=sleeps.append
    )
    with pytest.raises(GeocodingError):
        client.geocode("always fails")
    assert geo.calls == 3  # initial + 2 retries
    assert len(sleeps) == 2  # slept between attempts, never after the last


# --- NominatimGeocoder: response parsing (mocked HTTP) ----------------------


def _urlopen_returning(body):
    cm = MagicMock()
    cm.__enter__.return_value.read.return_value = json.dumps(body).encode("utf-8")
    return cm


def test_nominatim_parses_top_result():
    geo = NominatimGeocoder("http://geo.test/search", "Curbfeast/test", 5)
    body = [{"lat": "40.5", "lon": "-74.1", "display_name": "123 Main St, Town"}]
    with patch(
        "apps.core.geocoding.urllib.request.urlopen",
        return_value=_urlopen_returning(body),
    ):
        assert geo.geocode_once("123 Main St") == GeocodeResult(
            40.5, -74.1, "123 Main St, Town"
        )


def test_nominatim_no_results_returns_none():
    geo = NominatimGeocoder("http://geo.test/search", "Curbfeast/test", 5)
    with patch(
        "apps.core.geocoding.urllib.request.urlopen",
        return_value=_urlopen_returning([]),
    ):
        assert geo.geocode_once("nowhere at all") is None


def test_nominatim_transport_error_raises_geocoding_error():
    geo = NominatimGeocoder("http://geo.test/search", "Curbfeast/test", 5)
    with patch(
        "apps.core.geocoding.urllib.request.urlopen",
        side_effect=urllib.error.URLError("down"),
    ):
        with pytest.raises(GeocodingError):
            geo.geocode_once("123 Main St")


def test_nominatim_malformed_response_raises_geocoding_error():
    geo = NominatimGeocoder("http://geo.test/search", "Curbfeast/test", 5)
    body = [{"display_name": "missing lat/lon"}]
    with patch(
        "apps.core.geocoding.urllib.request.urlopen",
        return_value=_urlopen_returning(body),
    ):
        with pytest.raises(GeocodingError):
            geo.geocode_once("123 Main St")
