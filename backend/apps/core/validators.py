from django.core.exceptions import ValidationError

MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB


def validate_image_size(image):
    """Reject oversized image uploads at the form/serializer layer (before the
    bytes are decoded). EXIF stripping and resizing happen on save via
    apps.core.images.ProcessedImageField; private storage for PII evidence is
    still tracked in docs/architecture/security-checklist.md."""
    if image.size > MAX_IMAGE_SIZE:
        raise ValidationError("Image must be 5 MB or smaller.")
