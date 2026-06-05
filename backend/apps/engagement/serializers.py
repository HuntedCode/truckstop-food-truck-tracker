import json

from rest_framework import serializers

from apps.appearances.models import Appearance
from apps.trucks.models import Truck
from apps.trucks.serializers import TruckSerializer

from .models import EngagementEvent, Follow


class FollowSerializer(serializers.ModelSerializer):
    # Only publicly-visible trucks can be followed (consistent with discovery).
    truck = serializers.SlugRelatedField(
        slug_field="slug",
        queryset=Truck.objects.filter(
            status=Truck.Status.ACTIVE,
            verification_status=Truck.VerificationStatus.VERIFIED,
        ),
    )
    truck_detail = TruckSerializer(source="truck", read_only=True)

    class Meta:
        model = Follow
        fields = ["id", "truck", "truck_detail", "notifications_muted", "created_at"]
        read_only_fields = ["id", "created_at"]

    def update(self, instance, validated_data):
        # A follow's truck is immutable; PATCH only toggles notifications_muted.
        validated_data.pop("truck", None)
        return super().update(instance, validated_data)


class EngagementEventSerializer(serializers.ModelSerializer):
    """Ingest of an analytics event. user is set server-side."""

    # Restrict to publicly-visible objects (no metric pollution / PK probing).
    truck = serializers.PrimaryKeyRelatedField(
        queryset=Truck.objects.filter(
            status=Truck.Status.ACTIVE,
            verification_status=Truck.VerificationStatus.VERIFIED,
        ),
        required=False,
        allow_null=True,
    )
    appearance = serializers.PrimaryKeyRelatedField(
        queryset=Appearance.objects.public(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = EngagementEvent
        fields = [
            "id",
            "event_type",
            "truck",
            "appearance",
            "device_id",
            "metadata",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate_metadata(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("metadata must be a JSON object.")
        if len(json.dumps(value)) > 2048:
            raise serializers.ValidationError("metadata is too large.")
        return value
