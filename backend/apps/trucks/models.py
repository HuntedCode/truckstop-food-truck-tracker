from django.conf import settings
from django.db import models
from django.utils.text import slugify

from apps.core.models import TimeStampedModel


class Cuisine(TimeStampedModel):
    """Admin-curated lookup. Drives discovery filtering and the cold-start
    fallback imagery (icon + color) from the design system."""

    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(max_length=70, unique=True)
    icon = models.CharField(max_length=40, blank=True, help_text="Icon token.")
    color = models.CharField(max_length=7, blank=True, help_text="Hex, e.g. #E84A27.")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Truck(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        ACTIVE = "ACTIVE", "Active"
        PAUSED = "PAUSED", "Paused"

    class VerificationStatus(models.TextChoices):
        UNVERIFIED = "UNVERIFIED", "Unverified"
        PENDING = "PENDING", "Pending"
        VERIFIED = "VERIFIED", "Verified"
        REJECTED = "REJECTED", "Rejected"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="trucks"
    )
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    primary_cuisine = models.ForeignKey(
        Cuisine,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="primary_trucks",
    )
    cuisine_tags = models.ManyToManyField(
        Cuisine, blank=True, related_name="tagged_trucks"
    )
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to="trucks/logos/", null=True, blank=True)
    hero_image = models.ImageField(upload_to="trucks/heroes/", null=True, blank=True)
    timezone = models.CharField(max_length=64, default="America/Chicago")
    website = models.URLField(blank=True)
    phone = models.CharField(max_length=32, blank=True)
    instagram = models.CharField(max_length=64, blank=True)
    accepts_catering_inquiries = models.BooleanField(default=False)
    status = models.CharField(
        max_length=8, choices=Status.choices, default=Status.DRAFT
    )
    verification_status = models.CharField(
        max_length=10,
        choices=VerificationStatus.choices,
        default=VerificationStatus.UNVERIFIED,
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._unique_slug()
        super().save(*args, **kwargs)

    def _unique_slug(self):
        base = slugify(self.name) or "truck"
        slug = base
        suffix = 2
        while Truck.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            slug = f"{base}-{suffix}"
            suffix += 1
        return slug

    @property
    def is_publicly_visible(self):
        """Public discovery requires an active, verified truck (the gate)."""
        return (
            self.status == self.Status.ACTIVE
            and self.verification_status == self.VerificationStatus.VERIFIED
        )


class TruckVerification(TimeStampedModel):
    """Audit trail for the owner-verification flow. Reviewed in Django admin
    for the MVP. See docs/features/owner-verification.md."""

    class Method(models.TextChoices):
        PERMIT = "PERMIT", "Permit / license"
        SOCIAL = "SOCIAL", "Social account"
        LIVE_PHOTO = "LIVE_PHOTO", "Coded live photo"
        CALL = "CALL", "Call / video"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    class Reason(models.TextChoices):
        BLURRY = "BLURRY", "Image too blurry"
        NAME_MISMATCH = "NAME_MISMATCH", "Name mismatch"
        EXPIRED = "EXPIRED", "Document expired"
        SOCIAL_UNVERIFIED = "SOCIAL_UNVERIFIED", "Could not verify social"
        NEED_MORE_INFO = "NEED_MORE_INFO", "Need more info"

    truck = models.ForeignKey(
        Truck, on_delete=models.CASCADE, related_name="verifications"
    )
    method = models.CharField(max_length=12, choices=Method.choices)
    evidence_image = models.ImageField(
        upload_to="verifications/", null=True, blank=True
    )
    evidence_note = models.TextField(blank=True)
    status = models.CharField(
        max_length=8, choices=Status.choices, default=Status.PENDING
    )
    reason = models.CharField(max_length=20, choices=Reason.choices, blank=True)
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_verifications",
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.truck} verification ({self.status})"

    def approve(self, reviewer=None):
        """Approve this submission and mark the truck verified."""
        self.status = self.Status.APPROVED
        self.reason = ""
        if reviewer is not None:
            self.reviewer = reviewer
        self.save()
        self.truck.verification_status = Truck.VerificationStatus.VERIFIED
        self.truck.save(update_fields=["verification_status", "updated_at"])

    def reject(self, reason, reviewer=None, notes=""):
        """Reject with a structured reason (maps to a friendly owner message)."""
        if reason not in self.Reason.values:
            raise ValueError(f"Invalid rejection reason: {reason!r}")
        self.status = self.Status.REJECTED
        self.reason = reason
        if reviewer is not None:
            self.reviewer = reviewer
        if notes:
            self.notes = notes
        self.save()
        self.truck.verification_status = Truck.VerificationStatus.REJECTED
        self.truck.save(update_fields=["verification_status", "updated_at"])
