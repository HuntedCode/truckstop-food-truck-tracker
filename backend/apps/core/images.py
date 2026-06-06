"""Image upload hardening: strip metadata (EXIF, including GPS) and cap size.

User-supplied photos (truck logos/heroes, verification evidence) can embed
precise GPS coordinates and personal metadata, can be arbitrarily large on
screen (decompression bombs: tiny on disk, enormous decoded), and otherwise be
an attack surface. ``ProcessedImageField`` re-encodes every new upload from
decoded pixels at the **model layer**, so the protection applies no matter the
entry point (web form, DRF API, or admin).

The control **fails closed**: an image that cannot be safely processed (a bomb,
a corrupt or hostile file, an unencodable mode) is rejected, never stored
unprocessed. For graceful UX, the same checks run as a validator at the
form/serializer layer (see apps.core.validators.validate_processable_image), so
the common entry points reject with a message instead of erroring at save time.
See docs/architecture/security-checklist.md.
"""

import io
import os

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import models
from PIL import Image, ImageOps, PngImagePlugin

# Longest-side cap (px) for stored images. Large enough to keep permits/menus
# legible, small enough to bound storage and rendering cost.
MAX_IMAGE_DIMENSION = 2000

# Reject a source image whose declared pixel count exceeds this BEFORE decoding
# it (the pixel count, hence memory, is realized at decode). Comfortably above a
# default phone photo (~12 MP) while rejecting decompression bombs.
MAX_SOURCE_PIXELS = 30_000_000

# Lower Pillow's global ceiling too, as a backstop for any decode path we don't
# own (e.g. Django's own ImageField validation).
Image.MAX_IMAGE_PIXELS = MAX_SOURCE_PIXELS

# Re-saved as themselves; any other decodable format is normalized to JPEG.
_PRESERVED_FORMATS = {"JPEG", "PNG", "WEBP"}
_EXTENSIONS = {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp"}


def process_image(file, max_dimension=MAX_IMAGE_DIMENSION):
    """Return ``(ContentFile, format)`` for a metadata-stripped, dimension-capped
    copy of an image upload, or ``None`` if it cannot be safely processed
    (undecodable, a decompression bomb, or unencodable).

    Re-encoding from decoded pixels with a cleared ``info`` dict, and no EXIF
    passed to ``save()``, is what guarantees EXIF/GPS, XMP, ICC, and PNG text
    chunks are gone.
    """
    try:
        if hasattr(file, "seek"):
            file.seek(0)
        image = Image.open(file)
        width, height = image.size
        if width * height > MAX_SOURCE_PIXELS:
            return None  # decompression bomb / oversized: reject before decode
        image.load()
    except Exception:
        return None

    source_format = (image.format or "JPEG").upper()
    image = ImageOps.exif_transpose(image)  # bake orientation, then drop EXIF
    if max(image.size) > max_dimension:
        image.thumbnail((max_dimension, max_dimension))
    # Drop ALL embedded metadata at once (EXIF/GPS, XMP, ICC profile, PNG text).
    image.info = {}

    save_format = source_format if source_format in _PRESERVED_FORMATS else "JPEG"
    params = {}
    if save_format == "JPEG":
        if image.mode not in ("RGB", "L"):
            image = image.convert("RGB")
        params = {"quality": 85, "optimize": True}
    elif save_format == "PNG":
        params = {"pnginfo": PngImagePlugin.PngInfo()}  # explicitly empty: no text
    elif image.mode == "P":
        image = image.convert("RGBA")  # palette WEBP needs a true-color mode

    buffer = io.BytesIO()
    try:
        image.save(buffer, format=save_format, **params)
    except Exception:
        return None
    return ContentFile(buffer.getvalue()), save_format


def _with_extension(name, save_format):
    """Make the stored filename's extension match the re-encoded format (a file
    normalized to JPEG should not keep a misleading .gif name)."""
    root, _ = os.path.splitext(name)
    return root + _EXTENSIONS.get(save_format, ".jpg")


class ProcessedImageField(models.ImageField):
    """ImageField that strips metadata and caps dimensions on every new upload,
    at the model layer so all entry points are covered, and **fails closed**:
    an image that cannot be processed is rejected, never stored unprocessed.
    Existing (unchanged) files are left untouched."""

    def pre_save(self, model_instance, add):
        # Mirror FileField.pre_save, but re-encode a freshly uploaded file before
        # it is committed to storage (the base would commit it as-is).
        file = getattr(model_instance, self.attname)
        if file and not file._committed and getattr(file, "file", None) is not None:
            result = process_image(file.file)
            if result is None:
                raise ValidationError(
                    "This image could not be processed. Upload a valid photo."
                )
            content, save_format = result
            file.save(_with_extension(file.name, save_format), content, save=False)
        return file
