import factory

from apps.accounts.tests.factories import UserFactory
from apps.notifications.models import NotificationPreference, PushToken


class NotificationPreferenceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = NotificationPreference

    user = factory.SubFactory(UserFactory)


class PushTokenFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PushToken

    user = factory.SubFactory(UserFactory)
    token = factory.Sequence(lambda n: f"ExponentPushToken[{n}]")
    platform = PushToken.Platform.IOS
