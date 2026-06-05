from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel


class NotificationPreference(TimeStampedModel):
    """Per-user global notification settings. Per-truck mute lives on
    Follow.notifications_muted."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notification_preference",
    )
    push_enabled = models.BooleanField(default=True)
    email_marketing_opt_in = models.BooleanField(default=False)

    def __str__(self):
        return f"Notification prefs for {self.user}"


class PushToken(TimeStampedModel):
    """A device's Expo push token."""

    class Platform(models.TextChoices):
        IOS = "IOS", "iOS"
        ANDROID = "ANDROID", "Android"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="push_tokens",
    )
    token = models.CharField(max_length=255, unique=True)
    platform = models.CharField(max_length=8, choices=Platform.choices)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.platform} token for {self.user}"
