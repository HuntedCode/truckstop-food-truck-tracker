import factory

from apps.accounts.models import User


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        skip_postgeneration_save = True

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    role = User.Role.CUSTOMER
    display_name = factory.Faker("name")

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        self.set_password(extracted or "password123!")
        if create:
            self.save()


class OwnerFactory(UserFactory):
    role = User.Role.OWNER
