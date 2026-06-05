from rest_framework import generics, mixins, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import NotificationPreference, PushToken
from .serializers import NotificationPreferenceSerializer, PushTokenSerializer


class NotificationPreferenceView(generics.RetrieveUpdateAPIView):
    """The current user's notification settings (created on first access)."""

    serializer_class = NotificationPreferenceSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "patch", "head", "options"]

    def get_object(self):
        pref, _ = NotificationPreference.objects.get_or_create(user=self.request.user)
        return pref


class PushTokenViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """Register / list / remove the current user's device push tokens."""

    serializer_class = PushTokenSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PushToken.objects.filter(user=self.request.user).order_by("-created_at")

    def create(self, request, *args, **kwargs):
        # Re-registering a token (e.g. a device that switched accounts) upserts
        # it to the current user rather than failing the unique constraint.
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token, created = PushToken.objects.update_or_create(
            token=serializer.validated_data["token"],
            defaults={
                "user": request.user,
                "platform": serializer.validated_data["platform"],
                "is_active": True,
            },
        )
        out = self.get_serializer(token)
        return Response(
            out.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )
