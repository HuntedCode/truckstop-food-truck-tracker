from django.contrib.gis.geos import Point
from rest_framework.exceptions import ValidationError


def point_from_latlng(lat, lng):
    """Build a SRID 4326 Point from latitude/longitude, or None if either is
    missing. Raises a DRF ValidationError on non-numeric input.

    Note: PostGIS stores points as (x=longitude, y=latitude), so the order is
    flipped here on purpose. This is the one place that ordering lives.
    """
    if lat is None or lng is None:
        return None
    try:
        return Point(float(lng), float(lat), srid=4326)
    except (TypeError, ValueError):
        raise ValidationError("latitude/longitude must be numbers.")


def safe_point_from_latlng(lat, lng):
    """Like point_from_latlng but returns None instead of raising on missing or
    non-numeric input. For user-facing surfaces that should fall back gracefully
    rather than error (e.g. the public discovery page reading query params)."""
    try:
        return point_from_latlng(lat, lng)
    except ValidationError:
        return None
