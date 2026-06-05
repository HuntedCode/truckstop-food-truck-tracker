from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("apps.core.urls")),
    path("api/v1/auth/", include("apps.accounts.urls")),
    path("api/v1/", include("apps.trucks.urls")),
    path("api/v1/", include("apps.appearances.urls")),
    path("api/v1/", include("apps.engagement.urls")),
    path("api/v1/", include("apps.notifications.urls")),
    # Server-rendered web (owner dashboard) at the root.
    path("", include("apps.web.urls")),
]
