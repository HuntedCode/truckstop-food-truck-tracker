from django.contrib.gis.geos import Point
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError

from .models import Appearance
from .serializers import AppearanceSerializer

DEFAULT_RADIUS_KM = 5.0
MAX_RADIUS_KM = 50.0


class AppearanceViewSet(viewsets.ReadOnlyModelViewSet):
    """Public discovery of upcoming appearances of active, verified trucks.

    Proximity search: ?lat=<float>&lng=<float>&radius_km=<float>. With a point,
    results are filtered to the radius and sorted nearest-first with a
    distance_km annotation; without one, they are ordered by start time.
    """

    serializer_class = AppearanceSerializer

    def get_queryset(self):
        qs = (
            Appearance.objects.public()
            .upcoming()
            .select_related("truck", "truck__primary_cuisine")
            .prefetch_related("truck__cuisine_tags")
        )
        near = self._parse_near()
        if near is not None:
            point, radius_km = near
            return qs.nearby(point, radius_km)
        return qs.order_by("start_at")

    def _parse_near(self):
        params = self.request.query_params
        lat, lng = params.get("lat"), params.get("lng")
        if lat is None and lng is None:
            return None
        if lat is None or lng is None:
            raise ValidationError("Both lat and lng are required for proximity search.")
        try:
            lat_f, lng_f = float(lat), float(lng)
            radius_km = float(params.get("radius_km", DEFAULT_RADIUS_KM))
        except (TypeError, ValueError):
            raise ValidationError("lat, lng, and radius_km must be numbers.")
        if not (-90 <= lat_f <= 90 and -180 <= lng_f <= 180):
            raise ValidationError("lat must be in [-90, 90] and lng in [-180, 180].")
        if not (0 < radius_km <= MAX_RADIUS_KM):
            raise ValidationError(f"radius_km must be in (0, {MAX_RADIUS_KM}].")
        return Point(lng_f, lat_f, srid=4326), radius_km
