from datetime import timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework.test import APIClient

from apps.accounts.models import EmailVerificationToken, User


@pytest.mark.django_db
def test_registration_sends_verification_email_and_token():
    with patch("apps.accounts.views.send_mail") as send_mail:
        response = APIClient().post(
            reverse("v1:accounts:register"),
            {"email": "new@example.com", "password": "A-strong-password-123"},
            format="json",
        )

    assert response.status_code == 201
    assert send_mail.called
    assert EmailVerificationToken.objects.filter(user__email="new@example.com").exists()


@pytest.mark.django_db
def test_verify_email_is_one_time_and_marks_user_verified():
    user = User.objects.create_user("new@example.com", "A-strong-password-123")
    verification = EmailVerificationToken.objects.create(
        user=user,
        token_hash="a" * 64,
        expires_at=timezone.now() + timedelta(hours=1),
    )
    with patch("apps.accounts.views.hashlib.sha256") as sha256:
        sha256.return_value.hexdigest.return_value = verification.token_hash
        client = APIClient()
        response = client.post(
            reverse("v1:accounts:verify-email"), {"token": "raw-token"}, format="json"
        )

    assert response.status_code == 200
    assert response.json()["email"] == user.email
    user.refresh_from_db()
    assert user.is_email_verified

    response = client.post(
        reverse("v1:accounts:verify-email"), {"token": "raw-token"}, format="json"
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_password_reset_request_does_not_disclose_account_existence(user):
    with patch("apps.accounts.views.send_mail") as send_mail:
        response = APIClient().post(
            reverse("v1:accounts:password-reset"),
            {"email": user.email},
            format="json",
        )
        assert response.status_code == 200
        assert send_mail.called

        response = APIClient().post(
            reverse("v1:accounts:password-reset"),
            {"email": "missing@example.com"},
            format="json",
        )

    assert response.status_code == 200
    assert response.json() == {
        "message": "If an account exists, reset instructions have been sent."
    }
    assert send_mail.call_count == 1


@pytest.mark.django_db
def test_password_reset_confirm_changes_password(user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    response = APIClient().post(
        reverse("v1:accounts:password-reset-confirm"),
        {"uid": uid, "token": token, "new_password": "New-strong-password-123"},
        format="json",
    )

    assert response.status_code == 200
    user.refresh_from_db()
    assert user.check_password("New-strong-password-123")
