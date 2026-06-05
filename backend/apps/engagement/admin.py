from django.contrib import admin

from .models import EngagementEvent, Follow


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ("customer", "truck", "notifications_muted", "created_at")
    list_filter = ("notifications_muted",)
    search_fields = ("customer__email", "truck__name")
    autocomplete_fields = ("customer", "truck")


@admin.register(EngagementEvent)
class EngagementEventAdmin(admin.ModelAdmin):
    list_display = ("event_type", "truck", "user", "created_at")
    list_filter = ("event_type",)
    search_fields = ("truck__name", "user__email")
    autocomplete_fields = ("user", "truck", "appearance")
    readonly_fields = ("created_at", "updated_at")
