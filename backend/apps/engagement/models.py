from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel


class Follow(TimeStampedModel):
    """A customer following a truck (the community graph)."""

    # Should be a CUSTOMER account; enforced at the serializer/permission layer
    # (not yet built). See docs/architecture/data-model.md.
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="follows"
    )
    truck = models.ForeignKey(
        "trucks.Truck", on_delete=models.CASCADE, related_name="followers"
    )
    notifications_muted = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["customer", "truck"], name="unique_follow")
        ]

    def __str__(self):
        return f"{self.customer} -> {self.truck}"


class EngagementEvent(TimeStampedModel):
    """Append-only analytics substrate. Cheap to log now, expensive to
    backfill later. See docs/architecture/cross-cutting-concerns.md."""

    class EventType(models.TextChoices):
        TRUCK_VIEW = "TRUCK_VIEW", "Truck view"
        PROFILE_VIEW = "PROFILE_VIEW", "Profile view"
        SEARCH = "SEARCH", "Search"
        DIRECTIONS_TAP = "DIRECTIONS_TAP", "Directions tap"
        FOLLOW = "FOLLOW", "Follow"
        UNFOLLOW = "UNFOLLOW", "Unfollow"
        APPEARANCE_VIEW = "APPEARANCE_VIEW", "Appearance view"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="engagement_events",
    )
    device_id = models.CharField(max_length=64, blank=True)
    truck = models.ForeignKey(
        "trucks.Truck",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="engagement_events",
    )
    appearance = models.ForeignKey(
        "appearances.Appearance",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="engagement_events",
    )
    event_type = models.CharField(max_length=20, choices=EventType.choices)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["truck", "event_type", "created_at"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.event_type} ({self.created_at:%Y-%m-%d})"

    @classmethod
    def log(
        cls,
        event_type,
        *,
        user=None,
        truck=None,
        appearance=None,
        device_id="",
        metadata=None,
    ):
        """Append one analytics event. The single place app code records
        engagement, so the web and API surfaces log identically."""
        return cls.objects.create(
            event_type=event_type,
            user=user,
            truck=truck,
            appearance=appearance,
            device_id=device_id,
            metadata=metadata or {},
        )
