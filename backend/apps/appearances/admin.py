from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin

from .models import Appearance, PresenceConfirmation


@admin.register(Appearance)
class AppearanceAdmin(GISModelAdmin):
    list_display = (
        "truck",
        "location_name",
        "start_at",
        "end_at",
        "status",
        "last_confirmed_at",
    )
    list_filter = ("status",)
    search_fields = ("truck__name", "address", "location_name")
    autocomplete_fields = ("truck",)


@admin.register(PresenceConfirmation)
class PresenceConfirmationAdmin(GISModelAdmin):
    list_display = ("appearance", "source", "kind", "confirmed_by", "created_at")
    list_filter = ("source", "kind")
