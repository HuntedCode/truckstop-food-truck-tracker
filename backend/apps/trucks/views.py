from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.permissions import IsOwnerRole

from .models import Cuisine, Truck
from .serializers import (
    CuisineSerializer,
    TruckSerializer,
    TruckWriteSerializer,
    VerificationSubmitSerializer,
)


class CuisineViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Cuisine.objects.filter(is_active=True)
    serializer_class = CuisineSerializer
    pagination_class = None  # small, curated lookup


class TruckViewSet(viewsets.ReadOnlyModelViewSet):
    """Public discovery of trucks. Only active, verified trucks are visible
    (the trust gate). Optional ?cuisine=<slug> filter."""

    serializer_class = TruckSerializer
    lookup_field = "slug"

    def get_queryset(self):
        qs = (
            Truck.objects.filter(
                status=Truck.Status.ACTIVE,
                verification_status=Truck.VerificationStatus.VERIFIED,
            )
            .select_related("primary_cuisine")
            .prefetch_related("cuisine_tags")
        )
        cuisine = self.request.query_params.get("cuisine")
        if cuisine:
            qs = qs.filter(primary_cuisine__slug=cuisine)
        return qs


class OwnerTruckViewSet(viewsets.ModelViewSet):
    """Owner management of their own trucks (including drafts). Scoped to the
    requesting owner, so another owner's trucks are simply not found."""

    serializer_class = TruckWriteSerializer
    permission_classes = [IsOwnerRole]
    lookup_field = "slug"
    http_method_names = ["get", "post", "put", "patch", "head", "options", "trace"]

    def get_queryset(self):
        return (
            Truck.objects.filter(owner=self.request.user)
            .select_related("primary_cuisine")
            .prefetch_related("cuisine_tags")
        )

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=["post"])
    def request_verification(self, request, slug=None):
        """Submit verification evidence; moves the truck to PENDING review.

        Disallowed while already pending or verified (no queue spam or
        self-demotion). Resubmission is allowed from UNVERIFIED or REJECTED.
        """
        truck = self.get_object()
        if truck.verification_status in (
            Truck.VerificationStatus.PENDING,
            Truck.VerificationStatus.VERIFIED,
        ):
            return Response(
                {"detail": "Verification is already pending or approved."},
                status=status.HTTP_409_CONFLICT,
            )
        serializer = VerificationSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(truck=truck)
        truck.verification_status = Truck.VerificationStatus.PENDING
        truck.save(update_fields=["verification_status", "updated_at"])
        return Response(serializer.data, status=status.HTTP_201_CREATED)
