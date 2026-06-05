from rest_framework.routers import SimpleRouter

from .views import CuisineViewSet, OwnerTruckViewSet, TruckViewSet

router = SimpleRouter()
router.register("cuisines", CuisineViewSet, basename="cuisine")
router.register("trucks", TruckViewSet, basename="truck")
router.register("owner/trucks", OwnerTruckViewSet, basename="owner-truck")

urlpatterns = router.urls
