import factory
from django.utils import timezone

from apps.accounts.models import User


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    email_verified_at = factory.LazyFunction(timezone.now)
    password = factory.PostGenerationMethodCall("set_password", "Str0ng-pass-123")
