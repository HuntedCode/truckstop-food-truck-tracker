from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import EngagementEventCreateView, FollowViewSet

router = SimpleRouter()
router.register("follows", FollowViewSet, basename="follow")

urlpatterns = router.urls + [
    path("events/", EngagementEventCreateView.as_view(), name="event-create"),
]
