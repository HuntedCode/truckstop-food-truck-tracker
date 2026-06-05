import factory
from django.utils.text import slugify

from apps.accounts.tests.factories import OwnerFactory
from apps.trucks.models import Cuisine, Truck, TruckVerification


class CuisineFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Cuisine
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: f"Cuisine {n}")
    slug = factory.LazyAttribute(lambda o: slugify(o.name))
    icon = "taco"
    color = "#E84A27"


class TruckFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Truck

    owner = factory.SubFactory(OwnerFactory)
    name = factory.Sequence(lambda n: f"Truck {n}")
    primary_cuisine = factory.SubFactory(CuisineFactory)
    # Default to a live, discoverable truck; verification-flow tests override.
    status = Truck.Status.ACTIVE
    verification_status = Truck.VerificationStatus.VERIFIED


class TruckVerificationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TruckVerification

    truck = factory.SubFactory(TruckFactory)
    method = TruckVerification.Method.PERMIT
    evidence_note = "permit #12345"
