from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import NotificationPreferenceView, PushTokenViewSet

router = SimpleRouter()
router.register("push-tokens", PushTokenViewSet, basename="push-token")

urlpatterns = router.urls + [
    path(
        "notification-preference/",
        NotificationPreferenceView.as_view(),
        name="notification-preference",
    ),
]
