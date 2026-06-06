"""Image upload hardening: strip metadata (EXIF, including GPS) and cap size.

User-supplied photos (truck logos/heroes, verification evidence) can embed
precise GPS coordinates and personal metadata in EXIF, and can be arbitrarily
large. ``ProcessedImageField`` re-encodes every new upload from pixels at the
**model layer**, so the protection applies no matter the entry point (web form,
DRF API, or Django admin). See docs/architecture/security-checklist.md.
"""

import io

from django.core.files.base import ContentFile
from django.db import models
from PIL import Image, ImageOps

# Longest-side cap (px). Large enough to keep permits/menus legible, small
# enough to bound storage and rendering cost.
MAX_IMAGE_DIMENSION = 2000

# Re-saved as themselves; any other decodable format is normalized to JPEG.
_PRESERVED_FORMATS = {"JPEG", "PNG", "WEBP"}


def process_image(file, max_dimension=MAX_IMAGE_DIMENSION):
    """Return a metadata-stripped, dimension-capped copy of an image upload as a
    ContentFile, or None if the input is not a decodable image.

    Re-encoding from decoded pixels, without passing EXIF and after dropping any
    residual metadata from ``info``, is what guarantees GPS/EXIF is gone.
    """
    try:
        if hasattr(file, "seek"):
            file.seek(0)
        image = Image.open(file)
        image.load()
    except Exception:
        return None
    source_format = (image.format or "JPEG").upper()
    # Bake in the orientation tag, then strip all residual metadata so save()
    # cannot re-embed it.
    image = ImageOps.exif_transpose(image)
    if max(image.size) > max_dimension:
        image.thumbnail((max_dimension, max_dimension))
    image.info.pop("exif", None)
    image.info.pop("xmp", None)
    save_format = source_format if source_format in _PRESERVED_FORMATS else "JPEG"
    params = {}
    if save_format == "JPEG":
        if image.mode not in ("RGB", "L"):
            image = image.convert("RGB")
        params = {"quality": 85, "optimize": True}
    buffer = io.BytesIO()
    try:
        image.save(buffer, format=save_format, **params)
    except Exception:
        return None
    return ContentFile(buffer.getvalue())


class ProcessedImageField(models.ImageField):
    """ImageField that strips metadata and caps dimensions on every new upload,
    at the model layer so all entry points are covered. Existing (unchanged)
    files are left untouched."""

    def pre_save(self, model_instance, add):
        # Mirror FileField.pre_save, but re-encode a freshly uploaded file
        # before it is committed to storage (the base would commit it as-is).
        file = getattr(model_instance, self.attname)
        if file and not file._committed and getattr(file, "file", None) is not None:
            processed = process_image(file.file)
            content = processed if processed is not None else file.file
            file.save(file.name, content, save=False)
        return file
