from django.core.exceptions import ValidationError

MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB


def validate_image_size(image):
    """Reject oversized image uploads. (EXIF stripping, resizing, and private
    storage for PII evidence are tracked as pre-prod work; see
    docs/architecture/cross-cutting-concerns.md.)"""
    if image.size > MAX_IMAGE_SIZE:
        raise ValidationError("Image must be 5 MB or smaller.")
