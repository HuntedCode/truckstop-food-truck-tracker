from django.contrib import admin

from .models import Cuisine, Truck, TruckVerification


@admin.register(Cuisine)
class CuisineAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Truck)
class TruckAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "owner",
        "primary_cuisine",
        "status",
        "verification_status",
    )
    list_filter = ("status", "verification_status", "primary_cuisine")
    search_fields = ("name", "owner__email")
    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ("owner", "primary_cuisine")
    filter_horizontal = ("cuisine_tags",)


@admin.register(TruckVerification)
class TruckVerificationAdmin(admin.ModelAdmin):
    list_display = ("truck", "method", "status", "reason", "reviewer", "created_at")
    list_filter = ("status", "method", "reason")
    search_fields = ("truck__name",)
    autocomplete_fields = ("truck", "reviewer")
    actions = ["approve_selected"]

    @admin.action(description="Approve selected and mark trucks verified")
    def approve_selected(self, request, queryset):
        for verification in queryset:
            verification.approve(reviewer=request.user)
