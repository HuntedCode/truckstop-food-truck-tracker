from rest_framework import viewsets

from .models import Cuisine, Truck
from .serializers import CuisineSerializer, TruckSerializer


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
