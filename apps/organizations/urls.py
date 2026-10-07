from django.urls import path

from . import views

app_name = "organizations"

urlpatterns = [
    path("", views.list_organizations, name="list"),
    path("create/", views.create_organization, name="create"),
    path("invitations/accept/", views.accept_invitation, name="accept-invitation"),
    path("<uuid:organization_id>/invitations/", views.invite_member, name="invite"),
    path(
        "<uuid:organization_id>/invitations/<uuid:invitation_id>/",
        views.revoke_invitation,
        name="revoke-invitation",
    ),
    path(
        "<uuid:organization_id>/members/<uuid:membership_id>/",
        views.deactivate_member,
        name="deactivate-member",
    ),
]
