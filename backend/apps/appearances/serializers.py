from rest_framework import serializers

from apps.trucks.serializers import TruckSerializer

from .models import Appearance


class AppearanceSerializer(serializers.ModelSerializer):
    """Public discovery representation of an appearance."""

    truck = TruckSerializer(read_only=True)
    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()
    is_live = serializers.SerializerMethodField()
    is_verified_present = serializers.BooleanField(read_only=True)
    distance_km = serializers.SerializerMethodField()

    class Meta:
        model = Appearance
        fields = [
            "id",
            "truck",
            "address",
            "location_name",
            "latitude",
            "longitude",
            "start_at",
            "end_at",
            "status",
            "last_confirmed_at",
            "is_live",
            "is_verified_present",
            "distance_km",
        ]

    def get_latitude(self, obj):
        return obj.location.y

    def get_longitude(self, obj):
        return obj.location.x

    def get_is_live(self, obj):
        return obj.is_live()

    def get_distance_km(self, obj):
        # Annotated by AppearanceQuerySet.nearby(); absent on non-proximity lists.
        distance = getattr(obj, "distance", None)
        if distance is None:
            return None
        # GeoDjango Distance measure exposes .km; fall back if a raw number.
        km = getattr(distance, "km", None)
        if km is None:
            km = float(distance) / 1000.0
        return round(km, 3)
