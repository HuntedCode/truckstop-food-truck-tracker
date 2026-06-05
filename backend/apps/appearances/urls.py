from rest_framework.routers import SimpleRouter

from .views import AppearanceViewSet

router = SimpleRouter()
router.register("appearances", AppearanceViewSet, basename="appearance")

urlpatterns = router.urls
