import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from apps.core.images import MAX_IMAGE_DIMENSION, process_image


def _jpeg_with_exif(size=(120, 90)):
    """A JPEG carrying EXIF metadata (stands in for a photo with GPS tags)."""
    image = Image.new("RGB", size, "red")
    exif = Image.Exif()
    exif[0x0131] = "CurbfeastTestCamera"  # Software tag, round-trips reliably
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", exif=exif.tobytes())
    buffer.seek(0)
    return buffer


# --- process_image (pure) ---------------------------------------------------


def test_strips_exif_metadata():
    source = _jpeg_with_exif()
    assert dict(Image.open(source).getexif())  # sanity: the source HAS metadata
    source.seek(0)

    result = process_image(source)

    assert dict(Image.open(result).getexif()) == {}  # all metadata gone


def test_caps_oversized_dimensions():
    image = Image.new("RGB", (3000, 1000), "blue")
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    buffer.seek(0)

    out = Image.open(process_image(buffer))

    assert max(out.size) <= MAX_IMAGE_DIMENSION
    assert out.size[0] == 2000  # longest side capped, aspect ratio preserved


def test_keeps_small_image_dimensions():
    buffer = io.BytesIO()
    Image.new("RGB", (100, 80), "green").save(buffer, format="PNG")
    buffer.seek(0)

    out = Image.open(process_image(buffer))

    assert out.size == (100, 80)


def test_returns_none_for_non_image():
    assert process_image(io.BytesIO(b"definitely not an image")) is None


# --- ProcessedImageField (model layer, every entry point) -------------------


@pytest.mark.django_db
def test_uploaded_truck_logo_is_stripped_on_save(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    from apps.trucks.tests.factories import TruckFactory

    truck = TruckFactory()
    truck.logo = SimpleUploadedFile(
        "logo.jpg", _jpeg_with_exif().getvalue(), content_type="image/jpeg"
    )
    truck.save()

    truck.refresh_from_db()
    stored = Image.open(truck.logo.path)
    assert dict(stored.getexif()) == {}  # processed on the way into storage
