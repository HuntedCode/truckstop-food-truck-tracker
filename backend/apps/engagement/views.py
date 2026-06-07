from rest_framework import generics, mixins, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

from apps.core.permissions import IsCustomerRole

from .models import EngagementEvent, Follow
from .serializers import EngagementEventSerializer, FollowSerializer


class EventIngestAnonThrottle(AnonRateThrottle):
    """Tighter rate for the public anonymous event firehose. Applies only to
    anonymous requests; authenticated users fall under the user scope."""

    scope = "events_anon"


class FollowViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """A customer's follows. Scoped to the requesting customer. PATCH toggles
    notifications_muted; full replace (PUT) is disabled."""

    serializer_class = FollowSerializer
    permission_classes = [IsCustomerRole]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        return (
            Follow.objects.filter(customer=self.request.user)
            .select_related("truck", "truck__primary_cuisine")
            .prefetch_related("truck__cuisine_tags")
            .order_by("-created_at")
        )

    def perform_create(self, serializer):
        truck = serializer.validated_data["truck"]
        if Follow.objects.filter(customer=self.request.user, truck=truck).exists():
            raise ValidationError("You already follow this truck.")
        serializer.save(customer=self.request.user)
        EngagementEvent.log(
            EngagementEvent.EventType.FOLLOW, user=self.request.user, truck=truck
        )

    def perform_destroy(self, instance):
        truck = instance.truck
        super().perform_destroy(instance)
        EngagementEvent.log(
            EngagementEvent.EventType.UNFOLLOW, user=self.request.user, truck=truck
        )


class EngagementEventCreateView(generics.CreateAPIView):
    """Append-only analytics ingest. Anonymous allowed (device_id); the user is
    attached when authenticated."""

    serializer_class = EngagementEventSerializer
    permission_classes = [AllowAny]
    throttle_classes = [EventIngestAnonThrottle, UserRateThrottle]

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(user=user)
