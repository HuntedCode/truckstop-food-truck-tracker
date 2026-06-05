from rest_framework import serializers

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


class EngagementEventSerializer(serializers.ModelSerializer):
    """Ingest of an analytics event. user is set server-side."""

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
