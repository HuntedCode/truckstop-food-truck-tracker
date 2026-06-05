from rest_framework import serializers

from .models import Cuisine, Truck


class CuisineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cuisine
        fields = ["id", "name", "slug", "icon", "color"]


class TruckSerializer(serializers.ModelSerializer):
    """Public-facing truck representation (read-only)."""

    primary_cuisine = CuisineSerializer(read_only=True)
    cuisine_tags = CuisineSerializer(many=True, read_only=True)

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
            "verification_status",
        ]
