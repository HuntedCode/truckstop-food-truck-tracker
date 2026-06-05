from rest_framework.routers import SimpleRouter

from .views import CuisineViewSet, TruckViewSet

router = SimpleRouter()
router.register("cuisines", CuisineViewSet, basename="cuisine")
router.register("trucks", TruckViewSet, basename="truck")

urlpatterns = router.urls
