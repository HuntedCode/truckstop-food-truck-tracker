from datetime import timedelta

import factory
from django.contrib.gis.geos import Point
from django.utils import timezone

from apps.appearances.models import Appearance, PresenceConfirmation
from apps.trucks.tests.factories import TruckFactory


class AppearanceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Appearance

    truck = factory.SubFactory(TruckFactory)
    # Austin, TX by default.
    location = factory.LazyFunction(lambda: Point(-97.7431, 30.2672, srid=4326))
    address = "123 Test St"
    location_name = "Test Spot"
    # Live by default: started an hour ago, ends in two hours.
    start_at = factory.LazyFunction(lambda: timezone.now() - timedelta(hours=1))
    end_at = factory.LazyFunction(lambda: timezone.now() + timedelta(hours=2))


class PresenceConfirmationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PresenceConfirmation

    appearance = factory.SubFactory(AppearanceFactory)
    source = PresenceConfirmation.Source.OWNER
    kind = PresenceConfirmation.Kind.HERE_NOW
