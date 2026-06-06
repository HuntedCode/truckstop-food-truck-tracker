"""Address -> coordinates, behind a resilient, provider-neutral wrapper.

See ADR 0003: geocoding lives behind a normalized client so swapping providers
(Nominatim in dev, a storage-permitting provider in prod) is a config change,
not a rewrite. The client degrades gracefully:

- a blank address or no match returns ``None`` (a normal outcome), while
- a service/transport failure (after retries) raises ``GeocodingError``,

so callers can tell "address not found, refine it" from "service is down, try
again" and never surface a 500.
"""

import json
import logging
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

from django.conf import settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GeocodeResult:
    latitude: float
    longitude: float
    display_name: str


class GeocodingError(Exception):
    """The geocoding service failed (transport/HTTP/parse) after retries.
    Distinct from "no match", which is a normal ``None`` return."""


class NominatimGeocoder:
    """OpenStreetMap Nominatim adapter (free, used in dev). Nominatim requires a
    descriptive User-Agent and is rate-limited, which is fine for low-volume dev.
    One adapter method, ``geocode_once``; retries/backoff are the client's job."""

    def __init__(self, base_url, user_agent, timeout):
        self.base_url = base_url
        self.user_agent = user_agent
        self.timeout = timeout

    def geocode_once(self, address):
        """One request. Returns a GeocodeResult, or None for no match. Raises
        GeocodingError on a transport/HTTP/parse failure (retryable upstream)."""
        query = urllib.parse.urlencode({"q": address, "format": "json", "limit": 1})
        request = urllib.request.Request(
            f"{self.base_url}?{query}", headers={"User-Agent": self.user_agent}
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            raise GeocodingError(f"Nominatim request failed: {exc}") from exc
        if not payload:
            return None
        top = payload[0]
        try:
            return GeocodeResult(
                latitude=float(top["lat"]),
                longitude=float(top["lon"]),
                display_name=top.get("display_name", address),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise GeocodingError(f"Nominatim response malformed: {exc}") from exc


class GeocodingClient:
    """Provider-neutral geocoding with retry + exponential backoff and graceful
    degradation. Inject ``geocoder`` (and ``sleep``) in tests to avoid real HTTP
    and real delays."""

    def __init__(self, geocoder=None, max_retries=None, backoff=None, sleep=time.sleep):
        self.geocoder = geocoder or _build_geocoder()
        self.max_retries = (
            settings.GEOCODING_MAX_RETRIES if max_retries is None else max_retries
        )
        self.backoff = settings.GEOCODING_BACKOFF if backoff is None else backoff
        self._sleep = sleep

    def geocode(self, address):
        """Best-match GeocodeResult, or None for a blank address / no match.
        Raises GeocodingError if the service is unavailable after retries."""
        if not address or not address.strip():
            return None
        attempts = self.max_retries + 1
        last_exc = None
        for attempt in range(attempts):
            try:
                return self.geocoder.geocode_once(address.strip())
            except GeocodingError as exc:
                last_exc = exc
                if attempt < attempts - 1:
                    self._sleep(self.backoff * (2**attempt))
        logger.warning(
            "Geocoding failed for %r after %d attempt(s): %s",
            address,
            attempts,
            last_exc,
        )
        raise last_exc


def _build_geocoder():
    provider = settings.GEOCODING_PROVIDER
    if provider == "nominatim":
        return NominatimGeocoder(
            base_url=settings.NOMINATIM_BASE_URL,
            user_agent=settings.GEOCODING_USER_AGENT,
            timeout=settings.GEOCODING_TIMEOUT,
        )
    raise GeocodingError(f"Unknown geocoding provider: {provider!r}")


def geocode(address):
    """Convenience using a default client built from settings."""
    return GeocodingClient().geocode(address)
