from django.contrib import admin

from .models import NotificationPreference, PushToken


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ("user", "push_enabled", "email_marketing_opt_in")
    search_fields = ("user__email",)
    autocomplete_fields = ("user",)


@admin.register(PushToken)
class PushTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "platform", "is_active", "created_at")
    list_filter = ("platform", "is_active")
    search_fields = ("user__email",)
    autocomplete_fields = ("user",)
