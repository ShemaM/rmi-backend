import pytest
from django.db import IntegrityError

from apps.accounts.models import User


@pytest.mark.django_db
class TestUser:
    def test_create_user_normalises_email_and_hashes_password(self):
        user = User.objects.create_user("Jane.Doe@Example.COM", "Str0ng-pass-123")
        assert user.email == "jane.doe@example.com"
        assert user.check_password("Str0ng-pass-123")
        assert not user.is_staff

    def test_email_is_case_insensitively_unique(self):
        User.objects.create_user("a@example.com", "x")
        with pytest.raises(IntegrityError):
            User.objects.create(email="A@example.com")

    def test_create_superuser(self):
        admin = User.objects.create_superuser("admin@example.com", "x")
        assert admin.is_staff and admin.is_superuser
