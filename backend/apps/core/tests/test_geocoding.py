import json
import urllib.error
from unittest.mock import MagicMock, patch

import pytest
from django.core.exceptions import ImproperlyConfigured

from apps.core.geocoding import (
    GeocodeResult,
    GeocodingClient,
    GeocodingError,
    NominatimGeocoder,
    _build_geocoder,
    geocode,
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


def test_negative_max_retries_still_attempts_once():
    result = GeocodeResult(1.0, 2.0, "ok")
    geo = _FakeGeocoder([result])
    client = GeocodingClient(geocoder=geo, max_retries=-1, sleep=lambda s: None)
    assert client.geocode("x") == result
    assert geo.calls == 1


def test_negative_max_retries_failure_raises_geocoding_error_not_typeerror():
    geo = _FakeGeocoder([GeocodingError("boom")])
    client = GeocodingClient(geocoder=geo, max_retries=-1, sleep=lambda s: None)
    with pytest.raises(GeocodingError):  # never `raise None` -> TypeError
        client.geocode("x")
    assert geo.calls == 1


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


def test_nominatim_non_list_payload_raises_geocoding_error():
    # An error envelope (dict) instead of a list must not leak a raw KeyError.
    geo = NominatimGeocoder("http://geo.test/search", "Curbfeast/test", 5)
    with patch(
        "apps.core.geocoding.urllib.request.urlopen",
        return_value=_urlopen_returning({"error": "Unable to geocode"}),
    ):
        with pytest.raises(GeocodingError):
            geo.geocode_once("bad")


def test_nominatim_request_carries_query_and_user_agent():
    geo = NominatimGeocoder("http://geo.test/search", "Curbfeast/test-agent", 5)
    captured = {}

    def fake_urlopen(request, timeout=None):
        captured["url"] = request.full_url
        captured["ua"] = request.get_header("User-agent")
        return _urlopen_returning([{"lat": "1", "lon": "2", "display_name": "x"}])

    with patch("apps.core.geocoding.urllib.request.urlopen", side_effect=fake_urlopen):
        geo.geocode_once("Main & 5th")
    assert "format=json" in captured["url"] and "limit=1" in captured["url"]
    assert "q=Main" in captured["url"]  # address is query-encoded
    assert captured["ua"] == "Curbfeast/test-agent"  # Nominatim requires this


def test_non_http_base_url_is_rejected():
    with pytest.raises(ImproperlyConfigured):
        NominatimGeocoder("ftp://evil/search", "Curbfeast/test", 5)


def test_unknown_provider_raises_improperly_configured(settings):
    settings.GEOCODING_PROVIDER = "bogus"
    with pytest.raises(ImproperlyConfigured):
        _build_geocoder()


def test_module_level_geocode_uses_default_client():
    body = [{"lat": "39.1", "lon": "-94.6", "display_name": "KC"}]
    with patch(
        "apps.core.geocoding.urllib.request.urlopen",
        return_value=_urlopen_returning(body),
    ):
        assert geocode("Kansas City") == GeocodeResult(39.1, -94.6, "KC")


# --- search (multi-result, for the address picker) --------------------------


def test_nominatim_search_parses_and_skips_malformed():
    geo = NominatimGeocoder("http://geo.test/search", "Curbfeast/test", 5)
    body = [
        {"lat": "30.1", "lon": "-97.1", "display_name": "Austin A"},
        {"display_name": "missing coords"},  # one bad item shouldn't fail it all
        {"lat": "30.2", "lon": "-97.2", "display_name": "Austin B"},
    ]
    with patch(
        "apps.core.geocoding.urllib.request.urlopen",
        return_value=_urlopen_returning(body),
    ):
        results = geo.search("austin", 5)
    assert [r.display_name for r in results] == ["Austin A", "Austin B"]


def test_client_search_blank_returns_empty():
    client = GeocodingClient(geocoder=_FakeGeocoder([]), sleep=lambda s: None)
    assert client.search("   ") == []


def test_client_search_returns_results():
    class _Searcher:
        def search(self, address, limit):
            return [GeocodeResult(1.0, 2.0, "A"), GeocodeResult(3.0, 4.0, "B")]

    client = GeocodingClient(geocoder=_Searcher(), sleep=lambda s: None)
    assert [r.display_name for r in client.search("x")] == ["A", "B"]


def test_client_search_retries_then_raises():
    class _Down:
        def search(self, address, limit):
            raise GeocodingError("down")

    client = GeocodingClient(geocoder=_Down(), max_retries=1, sleep=lambda s: None)
    with pytest.raises(GeocodingError):
        client.search("x")
