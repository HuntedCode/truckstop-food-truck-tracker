from rest_framework.routers import SimpleRouter

from .views import AppearanceViewSet, OwnerAppearanceViewSet

router = SimpleRouter()
router.register("appearances", AppearanceViewSet, basename="appearance")
router.register(
    "owner/appearances", OwnerAppearanceViewSet, basename="owner-appearance"
)

urlpatterns = router.urls
