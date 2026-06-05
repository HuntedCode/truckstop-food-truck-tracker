from django.conf import settings
from django.conf.urls.static import static
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

if settings.DEBUG:
    # Serve user-uploaded media (truck logos/heroes) from the dev server.
    # Production serves media from object storage / a real web server.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
