from rest_framework.permissions import BasePermission

from .models import OrganizationMembership


class IsVerifiedUser(BasePermission):
    message = "Email verification is required."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_active
            and request.user.is_email_verified
        )


class IsOrganizationAdmin(BasePermission):
    message = "Organization administrator access is required."

    def has_object_permission(self, request, view, organization):
        return OrganizationMembership.objects.filter(
            organization=organization,
            user=request.user,
            role__in=[
                OrganizationMembership.Role.OWNER,
                OrganizationMembership.Role.ADMIN,
            ],
            is_active=True,
        ).exists()
