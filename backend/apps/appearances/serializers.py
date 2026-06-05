from rest_framework import serializers

from apps.core.geo import point_from_latlng
from apps.trucks.models import Truck
from apps.trucks.serializers import TruckSerializer

from .models import Appearance


class AppearanceSerializer(serializers.ModelSerializer):
    """Public discovery representation of an appearance."""

    truck = TruckSerializer(read_only=True)
    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()
    is_live = serializers.SerializerMethodField()
    is_verified_present = serializers.ReadOnlyField()
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


class AppearanceWriteSerializer(serializers.ModelSerializer):
    """Owner create/update serializer. Coordinates come from the owner's
    confirmed pin as latitude/longitude and are stored as a point."""

    truck = serializers.SlugRelatedField(
        slug_field="slug", queryset=Truck.objects.all()
    )
    latitude = serializers.FloatField(write_only=True)
    longitude = serializers.FloatField(write_only=True)

    class Meta:
        model = Appearance
        fields = [
            "id",
            "truck",
            "latitude",
            "longitude",
            "address",
            "location_name",
            "coordinates_confirmed",
            "start_at",
            "end_at",
            "status",
        ]
        read_only_fields = ["id"]

    def validate_truck(self, truck):
        request = self.context["request"]
        if truck.owner_id != request.user.id:
            raise serializers.ValidationError("You do not own this truck.")
        return truck

    def validate(self, attrs):
        if ("latitude" in attrs) != ("longitude" in attrs):
            raise serializers.ValidationError(
                "latitude and longitude must be provided together."
            )
        start = attrs.get("start_at", getattr(self.instance, "start_at", None))
        end = attrs.get("end_at", getattr(self.instance, "end_at", None))
        if start and end and end <= start:
            raise serializers.ValidationError("end_at must be after start_at.")
        return attrs

    def _build_point(self, validated_data):
        point = point_from_latlng(
            validated_data.pop("latitude", None),
            validated_data.pop("longitude", None),
        )
        if point is not None:
            validated_data["location"] = point
        return validated_data

    def create(self, validated_data):
        return super().create(self._build_point(validated_data))

    def update(self, instance, validated_data):
        return super().update(instance, self._build_point(validated_data))
