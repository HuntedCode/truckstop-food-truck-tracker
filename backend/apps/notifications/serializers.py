from rest_framework import serializers

from .models import NotificationPreference, PushToken


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = ["push_enabled", "email_marketing_opt_in"]


class PushTokenSerializer(serializers.ModelSerializer):
    # Declared explicitly to drop DRF's auto UniqueValidator so the view can
    # upsert a re-registered token. The DB unique constraint still guards it.
    token = serializers.CharField(max_length=255)

    class Meta:
        model = PushToken
        fields = ["id", "token", "platform", "is_active", "created_at"]
        read_only_fields = ["id", "is_active", "created_at"]
