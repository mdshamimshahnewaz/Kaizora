from django.urls import path

from .views import (
    IdentityLinkEndView,
    IdentityLinksView,
    ResourceChoicesView,
    ResourceFromMemberView,
    ResourceListView,
    ResourceView,
    TeamListView,
    TeamMembershipsView,
    TeamMembershipView,
    TeamView,
)

urlpatterns = [
    path("<uuid:org>/resources/choices/", ResourceChoicesView.as_view()),
    path("<uuid:org>/resources/from-member/", ResourceFromMemberView.as_view()),
    path("<uuid:org>/resources/", ResourceListView.as_view()),
    path("<uuid:org>/resources/<uuid:resource>/", ResourceView.as_view()),
    path("<uuid:org>/resources/<uuid:resource>/identity-links/", IdentityLinksView.as_view()),
    path(
        "<uuid:org>/resources/<uuid:resource>/identity-links/<uuid:link>/end/",
        IdentityLinkEndView.as_view(),
    ),
    path("<uuid:org>/teams/", TeamListView.as_view()),
    path("<uuid:org>/teams/<uuid:team>/", TeamView.as_view()),
    path("<uuid:org>/teams/<uuid:team>/memberships/", TeamMembershipsView.as_view()),
    path(
        "<uuid:org>/teams/<uuid:team>/memberships/<uuid:membership>/", TeamMembershipView.as_view()
    ),
]
