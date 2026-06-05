from rest_framework import serializers

from .models import Cuisine, Truck, TruckVerification


class CuisineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cuisine
        fields = ["id", "name", "slug", "icon", "color"]


class TruckSerializer(serializers.ModelSerializer):
    """Public-facing truck representation (read-only)."""

    primary_cuisine = CuisineSerializer(read_only=True)
    cuisine_tags = CuisineSerializer(many=True, read_only=True)
    is_verified = serializers.SerializerMethodField()

    class Meta:
        model = Truck
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "primary_cuisine",
            "cuisine_tags",
            "logo",
            "hero_image",
            "website",
            "phone",
            "instagram",
            "accepts_catering_inquiries",
            "is_verified",
        ]

    def get_is_verified(self, obj):
        return obj.verification_status == Truck.VerificationStatus.VERIFIED


class TruckWriteSerializer(serializers.ModelSerializer):
    """Owner-facing create/update serializer. owner is set from the request;
    slug and verification_status are managed server-side."""

    class Meta:
        model = Truck
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "primary_cuisine",
            "cuisine_tags",
            "logo",
            "hero_image",
            "timezone",
            "website",
            "phone",
            "instagram",
            "accepts_catering_inquiries",
            "status",
            "verification_status",
        ]
        read_only_fields = ["id", "slug", "verification_status"]


class VerificationSubmitSerializer(serializers.ModelSerializer):
    """An owner submits evidence for review (status starts PENDING)."""

    class Meta:
        model = TruckVerification
        fields = [
            "id",
            "method",
            "evidence_image",
            "evidence_note",
            "status",
            "created_at",
        ]
        read_only_fields = ["id", "status", "created_at"]
