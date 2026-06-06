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
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)

# Cap the geocoding response body so a hostile/buggy endpoint cannot exhaust
# memory (the request timeout bounds time, not bytes).
MAX_RESPONSE_BYTES = 1_000_000


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
        # Refuse non-HTTP schemes so a misconfigured base URL can't make urlopen
        # reach file://, ftp://, etc.
        if not base_url.lower().startswith(("http://", "https://")):
            raise ImproperlyConfigured(
                f"Geocoding base URL must be http(s), got {base_url!r}."
            )
        self.base_url = base_url
        self.user_agent = user_agent
        self.timeout = timeout

    def _fetch(self, limit, address):
        """Hit Nominatim and return the parsed JSON list. Raises GeocodingError
        on any transport/HTTP/parse failure (retryable upstream).

        Note: Nominatim allows ~1 req/sec and 429s on abuse. That is fine for
        our deliberate (button-press) use; a batch caller would need throttling
        and Retry-After handling (deferred)."""
        query = urllib.parse.urlencode({"q": address, "format": "json", "limit": limit})
        request = urllib.request.Request(
            f"{self.base_url}?{query}", headers={"User-Agent": self.user_agent}
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                body = response.read(MAX_RESPONSE_BYTES)
            payload = json.loads(body.decode("utf-8"))
        except (urllib.error.URLError, TimeoutError) as exc:
            raise GeocodingError(f"Nominatim request failed: {exc}") from exc
        except ValueError as exc:  # truncated/oversized body or non-JSON
            raise GeocodingError(f"Nominatim response malformed: {exc}") from exc
        return payload

    def geocode_once(self, address):
        """One request, best match. GeocodeResult or None; raises GeocodingError
        on transport/parse failure or a malformed top result."""
        payload = self._fetch(1, address)
        if not payload:
            return None
        try:
            top = payload[0]
            return GeocodeResult(
                latitude=float(top["lat"]),
                longitude=float(top["lon"]),
                display_name=top.get("display_name", address),
            )
        except (KeyError, IndexError, TypeError, ValueError, AttributeError) as exc:
            raise GeocodingError(f"Nominatim response malformed: {exc}") from exc

    def search(self, address, limit):
        """Up to ``limit`` candidate matches for an address-picker. Lenient: a
        single malformed item is skipped rather than failing the whole search."""
        payload = self._fetch(limit, address)
        if not isinstance(payload, list):
            return []
        results = []
        for item in payload[:limit]:
            try:
                results.append(
                    GeocodeResult(
                        latitude=float(item["lat"]),
                        longitude=float(item["lon"]),
                        display_name=item.get("display_name", address),
                    )
                )
            except (KeyError, TypeError, ValueError, AttributeError):
                continue
        return results


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

    def _attempt(self, fn, address):
        # Clamp so a misconfigured negative retry count still makes one attempt
        # and never falls through to `raise None`.
        attempts = max(1, self.max_retries + 1)
        last_exc = None
        for attempt in range(attempts):
            try:
                return fn()
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

    def geocode(self, address):
        """Best-match GeocodeResult, or None for a blank address / no match.
        Raises GeocodingError if the service is unavailable after retries."""
        if not address or not address.strip():
            return None
        return self._attempt(
            lambda: self.geocoder.geocode_once(address.strip()), address
        )

    def search(self, address, limit=5):
        """Up to ``limit`` candidate matches (for the address picker), or an
        empty list for a blank address. Raises GeocodingError after retries."""
        if not address or not address.strip():
            return []
        return self._attempt(
            lambda: self.geocoder.search(address.strip(), limit), address
        )


def _build_geocoder():
    provider = settings.GEOCODING_PROVIDER
    if provider == "nominatim":
        return NominatimGeocoder(
            base_url=settings.NOMINATIM_BASE_URL,
            user_agent=settings.GEOCODING_USER_AGENT,
            timeout=settings.GEOCODING_TIMEOUT,
        )
    raise ImproperlyConfigured(f"Unknown geocoding provider: {provider!r}")


def geocode(address):
    """Convenience using a default client built from settings."""
    return GeocodingClient().geocode(address)


def search(address, limit=5):
    """Convenience using a default client built from settings."""
    return GeocodingClient().search(address, limit)
