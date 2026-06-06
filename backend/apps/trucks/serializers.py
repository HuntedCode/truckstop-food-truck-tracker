from rest_framework import serializers

from apps.core.validators import validate_image_size, validate_processable_image

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

    logo = serializers.ImageField(
        required=False,
        allow_null=True,
        validators=[validate_image_size, validate_processable_image],
    )
    hero_image = serializers.ImageField(
        required=False,
        allow_null=True,
        validators=[validate_image_size, validate_processable_image],
    )

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

    evidence_image = serializers.ImageField(
        required=False,
        allow_null=True,
        validators=[validate_image_size, validate_processable_image],
    )

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

    def validate(self, attrs):
        if (
            not attrs.get("evidence_image")
            and not (attrs.get("evidence_note") or "").strip()
        ):
            raise serializers.ValidationError("Provide an evidence image or note.")
        return attrs
