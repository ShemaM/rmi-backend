import secrets
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from .models import Organization, OrganizationInvitation, OrganizationMembership
from .permissions import IsOrganizationAdmin, IsVerifiedUser
from .serializers import (
    InvitationAcceptSerializer,
    InvitationCreateSerializer,
    MembershipSerializer,
    OrganizationSerializer,
)


class OrganizationInviteThrottle(ScopedRateThrottle):
    scope = "organization_invite"


@extend_schema(
    tags=["organizations"], request=OrganizationSerializer, responses={201: OrganizationSerializer}
)
@api_view(["POST"])
@permission_classes([IsVerifiedUser])
def create_organization(request):
    serializer = OrganizationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    with transaction.atomic():
        organization = serializer.save()
        OrganizationMembership.objects.create(
            organization=organization,
            user=request.user,
            role=OrganizationMembership.Role.OWNER,
        )
    return Response(OrganizationSerializer(organization).data, status=status.HTTP_201_CREATED)


@extend_schema(tags=["organizations"], responses={200: MembershipSerializer(many=True)})
@api_view(["GET"])
@permission_classes([IsVerifiedUser])
def list_organizations(request):
    memberships = (
        OrganizationMembership.objects.filter(user=request.user, is_active=True)
        .select_related("organization")
        .order_by("organization__name")
    )
    return Response(MembershipSerializer(memberships, many=True).data)


@extend_schema(tags=["organizations"], request=InvitationCreateSerializer, responses={201: dict})
@api_view(["POST"])
@permission_classes([IsVerifiedUser])
@throttle_classes([OrganizationInviteThrottle])
def invite_member(request, organization_id):
    try:
        organization = Organization.objects.get(id=organization_id, is_active=True)
    except Organization.DoesNotExist:
        raise ValidationError({"organization": "Organization not found."}) from None
    if not IsOrganizationAdmin().has_object_permission(request, None, organization):
        raise PermissionDenied("Organization administrator access is required.")

    serializer = InvitationCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    email = serializer.validated_data["email"].lower().strip()
    if OrganizationMembership.objects.filter(
        organization=organization, user__email=email, is_active=True
    ).exists():
        raise ValidationError({"email": "This user is already a member."})

    raw_token = secrets.token_urlsafe(32)
    invitation = OrganizationInvitation.objects.create(
        organization=organization,
        email=email,
        role=serializer.validated_data["role"],
        invited_by=request.user,
        token_hash=OrganizationInvitation.hash_token(raw_token),
        expires_at=timezone.now() + timedelta(days=7),
    )
    send_mail(
        f"Invitation to join {organization.name}",
        f"Use this invitation token to join the organization: {raw_token}",
        settings.DEFAULT_FROM_EMAIL,
        [email],
    )
    return Response(
        {"id": invitation.id, "message": "Invitation sent."}, status=status.HTTP_201_CREATED
    )


@extend_schema(
    tags=["organizations"],
    request=InvitationAcceptSerializer,
    responses={200: MembershipSerializer},
)
@api_view(["POST"])
@permission_classes([IsVerifiedUser])
def accept_invitation(request):
    serializer = InvitationAcceptSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    token_hash = OrganizationInvitation.hash_token(serializer.validated_data["token"])
    with transaction.atomic():
        try:
            invitation = OrganizationInvitation.objects.select_for_update().select_related(
                "organization"
            ).get(token_hash=token_hash)
        except OrganizationInvitation.DoesNotExist:
            raise ValidationError({"token": "This invitation is invalid."}) from None
        if not invitation.is_valid:
            raise ValidationError({"token": "This invitation is invalid or expired."})
        if invitation.email != request.user.email:
            raise PermissionDenied("This invitation belongs to a different email address.")
        membership, _ = OrganizationMembership.objects.update_or_create(
            organization=invitation.organization,
            user=request.user,
            defaults={"role": invitation.role, "is_active": True},
        )
        invitation.accepted_at = timezone.now()
        invitation.save(update_fields=["accepted_at", "updated_at"])
    return Response(MembershipSerializer(membership).data)
