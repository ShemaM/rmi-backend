import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.models import User


@pytest.mark.django_db
class TestRegistration:
    def test_registers_user_without_exposing_password(self):
        response = APIClient().post(
            reverse("v1:accounts:register"),
            {
                "email": "Jane.Doe@example.com",
                "password": "A-strong-password-123",
                "first_name": "Jane",
                "last_name": "Doe",
            },
            format="json",
        )

        assert response.status_code == 201
        assert response.json()["email"] == "jane.doe@example.com"
        assert "password" not in response.json()
        assert User.objects.get(email="jane.doe@example.com").check_password(
            "A-strong-password-123"
        )

    def test_rejects_weak_password(self):
        response = APIClient().post(
            reverse("v1:accounts:register"),
            {"email": "jane@example.com", "password": "password"},
            format="json",
        )

        assert response.status_code == 400
        assert response.json()["error"]["code"] == "validation_error"


@pytest.mark.django_db
def test_login_me_and_logout(auth_client, user):
    client = APIClient()
    response = client.post(
        reverse("v1:accounts:login"),
        {"email": user.email, "password": "Str0ng-pass-123"},
        format="json",
    )
    assert response.status_code == 200

    response = client.get(reverse("v1:accounts:me"))
    assert response.status_code == 200
    assert response.json()["id"] == str(user.id)

    response = client.post(reverse("v1:accounts:logout"))
    assert response.status_code == 204
    assert client.get(reverse("v1:accounts:me")).status_code == 403


@pytest.mark.django_db
def test_login_rejects_invalid_credentials(user):
    response = APIClient().post(
        reverse("v1:accounts:login"),
        {"email": user.email, "password": "wrong-password"},
        format="json",
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "validation_error"
