from datetime import timedelta
from unittest.mock import patch

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.organizations.models import Organization, OrganizationInvitation, OrganizationMembership


def verified_user(email):
    user = User.objects.create_user(email, "Str0ng-pass-123")
    user.mark_email_verified()
    return user


@pytest.mark.django_db
def test_verified_user_can_create_and_list_organization():
    user = verified_user("owner@example.com")
    client = APIClient()
    client.force_authenticate(user)

    response = client.post(
        reverse("v1:organizations:create"),
        {"name": "RMI Institute", "organization_type": "academic", "country": "RW"},
        format="json",
    )
    assert response.status_code == 201
    organization_id = response.json()["id"]
    assert OrganizationMembership.objects.get(
        organization_id=organization_id, user=user
    ).role == "owner"

    response = client.get(reverse("v1:organizations:list"))
    assert response.status_code == 200
    assert response.json()[0]["organization"]["name"] == "RMI Institute"


@pytest.mark.django_db
def test_unverified_user_cannot_create_organization():
    user = User.objects.create_user("unverified@example.com", "Str0ng-pass-123")
    client = APIClient()
    client.force_authenticate(user)

    response = client.post(
        reverse("v1:organizations:create"),
        {"name": "Should Not Exist", "organization_type": "other"},
        format="json",
    )
    assert response.status_code == 403
    assert not Organization.objects.filter(name="Should Not Exist").exists()


@pytest.mark.django_db
def test_only_admin_can_invite_and_matching_email_can_accept():
    owner = verified_user("owner@example.com")
    invited = verified_user("member@example.com")
    outsider = verified_user("outsider@example.com")
    organization = Organization.objects.create(name="RMI Institute")
    OrganizationMembership.objects.create(
        organization=organization, user=owner, role=OrganizationMembership.Role.OWNER
    )
    client = APIClient()
    client.force_authenticate(owner)

    with patch("apps.organizations.views.send_mail") as send_mail:
        response = client.post(
            reverse("v1:organizations:invite", args=[organization.id]),
            {"email": invited.email, "role": "member"},
            format="json",
        )
    assert response.status_code == 201
    assert send_mail.called
    invitation = OrganizationInvitation.objects.get(organization=organization)

    client.force_authenticate(outsider)
    with patch("apps.organizations.views.send_mail") as send_mail:
        response = client.post(
            reverse("v1:organizations:invite", args=[organization.id]),
            {"email": "another@example.com", "role": "member"},
            format="json",
        )
    assert response.status_code == 403
    assert not send_mail.called

    client.force_authenticate(invited)
    response = client.post(
        reverse("v1:organizations:accept-invitation"),
        {"token": "wrong-token-that-is-long-enough"},
        format="json",
    )
    assert response.status_code == 400

    raw_token = "valid-token-that-is-long-enough"
    invitation.token_hash = OrganizationInvitation.hash_token(raw_token)
    invitation.save(update_fields=["token_hash", "updated_at"])
    response = client.post(
        reverse("v1:organizations:accept-invitation"),
        {"token": raw_token},
        format="json",
    )
    assert response.status_code == 200
    assert OrganizationMembership.objects.filter(
        organization=organization, user=invited, is_active=True
    ).exists()


@pytest.mark.django_db
def test_invitation_rejects_expired_and_wrong_email():
    owner = verified_user("owner2@example.com")
    outsider = verified_user("outsider2@example.com")
    organization = Organization.objects.create(name="RMI Institute 2")
    OrganizationMembership.objects.create(
        organization=organization, user=owner, role=OrganizationMembership.Role.OWNER
    )
    invitation = OrganizationInvitation.objects.create(
        organization=organization,
        email="member2@example.com",
        role="member",
        invited_by=owner,
        token_hash=OrganizationInvitation.hash_token("expired-token"),
        expires_at=timezone.now() - timedelta(minutes=1),
    )
    client = APIClient()
    client.force_authenticate(outsider)
    response = client.post(
        reverse("v1:organizations:accept-invitation"),
        {"token": "expired-token"},
        format="json",
    )
    assert response.status_code == 400
    invitation.refresh_from_db()
    assert invitation.accepted_at is None
