from datetime import timedelta

from django.conf import settings
from django.contrib.gis.db import models as gis_models
from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel
from apps.trucks.models import Truck


class AppearanceQuerySet(models.QuerySet):
    def public(self):
        """Only appearances of active, verified trucks (the discovery gate)."""
        return self.filter(
            status=Appearance.Status.SCHEDULED,
            truck__status=Truck.Status.ACTIVE,
            truck__verification_status=Truck.VerificationStatus.VERIFIED,
        )

    def upcoming(self, now=None):
        now = now or timezone.now()
        return self.filter(end_at__gte=now)

    def live(self, now=None):
        now = now or timezone.now()
        return self.filter(
            status=Appearance.Status.SCHEDULED, start_at__lte=now, end_at__gte=now
        )

    def nearby(self, point, radius_km):
        """Appearances within radius_km of point, nearest first.

        Does NOT apply the public visibility gate. For customer-facing
        discovery, chain off public(): Appearance.objects.public().nearby(...).
        """
        from django.contrib.gis.db.models.functions import Distance
        from django.contrib.gis.measure import D

        return (
            self.filter(location__dwithin=(point, D(km=radius_km)))
            .annotate(distance=Distance("location", point))
            .order_by("distance")
        )


class Appearance(TimeStampedModel):
    """A truck at a place over a time window. The product spine."""

    class Status(models.TextChoices):
        SCHEDULED = "SCHEDULED", "Scheduled"
        CANCELED = "CANCELED", "Canceled"

    truck = models.ForeignKey(
        Truck, on_delete=models.CASCADE, related_name="appearances"
    )
    location = gis_models.PointField(geography=True)
    address = models.CharField(max_length=255)
    location_name = models.CharField(max_length=120, blank=True)
    coordinates_confirmed = models.BooleanField(default=False)
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.SCHEDULED
    )
    last_confirmed_at = models.DateTimeField(null=True, blank=True)

    objects = AppearanceQuerySet.as_manager()

    class Meta:
        ordering = ["start_at"]
        indexes = [
            models.Index(fields=["truck", "start_at"]),
            models.Index(fields=["start_at", "end_at"]),
        ]

    def __str__(self):
        return f"{self.truck} @ {self.location_name or self.address}"

    def is_live(self, now=None):
        now = now or timezone.now()
        return (
            self.status == self.Status.SCHEDULED and self.start_at <= now <= self.end_at
        )

    @property
    def is_verified_present(self):
        """True when a recent owner confirmation makes the pin trustworthy."""
        if not self.last_confirmed_at:
            return False
        window = getattr(settings, "PRESENCE_FRESHNESS_WINDOW", timedelta(hours=2))
        return timezone.now() - self.last_confirmed_at <= window


class PresenceConfirmation(TimeStampedModel):
    """The confirmation log. MVP records owner "I'm here now"; extends to
    crowd-confirmation and feeds trust rank later."""

    class Source(models.TextChoices):
        OWNER = "OWNER", "Owner"
        CUSTOMER = "CUSTOMER", "Customer"

    class Kind(models.TextChoices):
        HERE_NOW = "HERE_NOW", "Here now"
        NOT_HERE = "NOT_HERE", "Not here"

    appearance = models.ForeignKey(
        Appearance, on_delete=models.CASCADE, related_name="confirmations"
    )
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="confirmations",
    )
    source = models.CharField(max_length=8, choices=Source.choices)
    kind = models.CharField(max_length=8, choices=Kind.choices, default=Kind.HERE_NOW)
    point = gis_models.PointField(geography=True, null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.appearance} {self.kind} ({self.source})"

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        # On creation of an owner "here now", denormalize onto the appearance for
        # cheap "verified present" reads, but only when this is the latest
        # confirmation (guards against out-of-order or re-saved rows).
        if (
            is_new
            and self.source == self.Source.OWNER
            and self.kind == self.Kind.HERE_NOW
        ):
            Appearance.objects.filter(pk=self.appearance_id).filter(
                models.Q(last_confirmed_at__isnull=True)
                | models.Q(last_confirmed_at__lt=self.created_at)
            ).update(last_confirmed_at=self.created_at)
