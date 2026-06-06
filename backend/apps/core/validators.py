from django.core.exceptions import ValidationError

MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB


def validate_image_size(image):
    """Reject oversized image uploads at the form/serializer layer (before the
    bytes are decoded). EXIF stripping and resizing happen on save via
    apps.core.images.ProcessedImageField; private storage for PII evidence is
    still tracked in docs/architecture/security-checklist.md."""
    if image.size > MAX_IMAGE_SIZE:
        raise ValidationError("Image must be 5 MB or smaller.")


def validate_processable_image(image):
    """Reject undecodable images and decompression bombs (small file, enormous
    pixel dimensions) at the form/serializer layer, so they fail gracefully with
    a message instead of erroring when ProcessedImageField processes them on
    save. Cheap: reads the header dimensions, not the full pixels."""
    # Imported lazily to avoid a circular import at app load.
    from PIL import Image

    from apps.core.images import MAX_SOURCE_PIXELS

    try:
        if hasattr(image, "seek"):
            image.seek(0)
        with Image.open(image) as opened:
            width, height = opened.size
    except Exception:
        raise ValidationError("Could not read the image. Upload a valid photo.")
    finally:
        if hasattr(image, "seek"):
            image.seek(0)
    if width * height > MAX_SOURCE_PIXELS:
        raise ValidationError("Image dimensions are too large. Try a smaller photo.")
