import factory

from apps.accounts.tests.factories import UserFactory
from apps.engagement.models import EngagementEvent, Follow
from apps.trucks.tests.factories import TruckFactory


class FollowFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Follow

    customer = factory.SubFactory(UserFactory)
    truck = factory.SubFactory(TruckFactory)


class EngagementEventFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EngagementEvent

    event_type = EngagementEvent.EventType.TRUCK_VIEW
    truck = factory.SubFactory(TruckFactory)
