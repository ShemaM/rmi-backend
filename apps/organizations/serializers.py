from rest_framework import serializers

from .models import Organization, OrganizationMembership


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ("id", "name", "organization_type", "country", "website", "is_active")
        read_only_fields = ("id", "is_active")


class MembershipSerializer(serializers.ModelSerializer):
    organization = OrganizationSerializer(read_only=True)

    class Meta:
        model = OrganizationMembership
        fields = ("id", "organization", "role", "is_active")
        read_only_fields = fields


class InvitationCreateSerializer(serializers.Serializer):
    email = serializers.EmailField()
    role = serializers.ChoiceField(
        choices=[
            (OrganizationMembership.Role.ADMIN, "Admin"),
            (OrganizationMembership.Role.MEMBER, "Member"),
        ],
        default=OrganizationMembership.Role.MEMBER,
    )


class InvitationAcceptSerializer(serializers.Serializer):
    token = serializers.CharField(trim_whitespace=True, min_length=20)
