import io

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image, PngImagePlugin

from apps.core import images
from apps.core.images import MAX_IMAGE_DIMENSION, process_image
from apps.core.validators import validate_processable_image


def _jpeg_with_exif(size=(120, 90)):
    """A JPEG carrying EXIF metadata (stands in for a photo with GPS tags)."""
    image = Image.new("RGB", size, "red")
    exif = Image.Exif()
    exif[0x0131] = "ChuckwagonTestCamera"  # Software tag, round-trips reliably
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", exif=exif.tobytes())
    buffer.seek(0)
    return buffer


def _open_processed(buffer):
    result = process_image(buffer)
    assert result is not None
    content, _ = result
    return Image.open(content)


# --- Metadata stripping -----------------------------------------------------


def test_strips_exif_metadata():
    source = _jpeg_with_exif()
    assert dict(Image.open(source).getexif())  # sanity: the source HAS metadata
    source.seek(0)
    assert dict(_open_processed(source).getexif()) == {}


def test_strips_png_text_chunks():
    image = Image.new("RGB", (60, 60), "blue")
    meta = PngImagePlugin.PngInfo()
    meta.add_text("Author", "secret-person")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", pnginfo=meta)
    buffer.seek(0)
    assert Image.open(buffer).text  # sanity: the source HAS a text chunk
    buffer.seek(0)
    assert _open_processed(buffer).text == {}  # stripped


# --- Dimensions -------------------------------------------------------------


def test_caps_oversized_dimensions():
    image = Image.new("RGB", (3000, 1000), "blue")
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    buffer.seek(0)
    out = _open_processed(buffer)
    assert max(out.size) <= MAX_IMAGE_DIMENSION
    assert out.size[0] == 2000  # longest side capped, aspect ratio preserved


def test_keeps_small_image_dimensions():
    buffer = io.BytesIO()
    Image.new("RGB", (100, 80), "green").save(buffer, format="PNG")
    buffer.seek(0)
    assert _open_processed(buffer).size == (100, 80)


def test_normalized_format_gets_matching_extension():
    # A GIF normalizes to JPEG; the stored name must not keep a misleading .gif.
    assert images._with_extension("evidence.gif", "JPEG") == "evidence.jpg"


# --- Failure / bomb: fail closed --------------------------------------------


def test_returns_none_for_non_image():
    assert process_image(io.BytesIO(b"definitely not an image")) is None


def test_rejects_decompression_bomb(monkeypatch):
    # Shrink the pixel ceiling so a small test image trips the guard cheaply.
    monkeypatch.setattr(images, "MAX_SOURCE_PIXELS", 100)
    buffer = io.BytesIO()
    Image.new("RGB", (50, 50), "red").save(buffer, format="PNG")  # 2500 px > 100
    buffer.seek(0)
    assert process_image(buffer) is None


# --- validate_processable_image: graceful rejection at the input layer -------


def test_validator_accepts_normal_image():
    buffer = io.BytesIO()
    Image.new("RGB", (100, 100), "red").save(buffer, format="JPEG")
    upload = SimpleUploadedFile("ok.jpg", buffer.getvalue(), content_type="image/jpeg")
    validate_processable_image(upload)  # does not raise


def test_validator_rejects_non_image():
    upload = SimpleUploadedFile("x.jpg", b"not an image", content_type="image/jpeg")
    with pytest.raises(ValidationError):
        validate_processable_image(upload)


def test_validator_rejects_bomb(monkeypatch):
    monkeypatch.setattr(images, "MAX_SOURCE_PIXELS", 100)
    buffer = io.BytesIO()
    Image.new("RGB", (50, 50), "red").save(buffer, format="JPEG")
    upload = SimpleUploadedFile("big.jpg", buffer.getvalue(), content_type="image/jpeg")
    with pytest.raises(ValidationError):
        validate_processable_image(upload)


# --- ProcessedImageField (model layer) --------------------------------------


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
    assert dict(Image.open(truck.logo.path).getexif()) == {}


@pytest.mark.django_db
def test_field_fails_closed_on_unprocessable_image(monkeypatch, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    from apps.trucks.tests.factories import TruckFactory

    monkeypatch.setattr(images, "process_image", lambda f: None)
    truck = TruckFactory()
    truck.logo = SimpleUploadedFile("x.jpg", b"bytes", content_type="image/jpeg")
    with pytest.raises(ValidationError):  # rejected, never stored unprocessed
        truck.save()


@pytest.mark.django_db
def test_unchanged_save_does_not_reprocess(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    from apps.trucks.tests.factories import TruckFactory

    buffer = io.BytesIO()
    Image.new("RGB", (80, 80), "green").save(buffer, format="PNG")
    truck = TruckFactory()
    truck.logo = SimpleUploadedFile(
        "logo.png", buffer.getvalue(), content_type="image/png"
    )
    truck.save()
    first_name = truck.logo.name

    truck.name = "Renamed"
    truck.save()  # logo is committed/unchanged -> must not re-save under a new name

    truck.refresh_from_db()
    assert truck.logo.name == first_name
