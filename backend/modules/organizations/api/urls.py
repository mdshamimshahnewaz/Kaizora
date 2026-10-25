from django.urls import path

from .views import (
    MembershipsView,
    MembershipView,
    OrganizationsView,
    OrganizationView,
    ProvisioningView,
    TransferOwnerView,
)

urlpatterns = [
    path("", OrganizationsView.as_view()),
    path("provisioning/", ProvisioningView.as_view()),
    path("<uuid:org>/", OrganizationView.as_view()),
    path("<uuid:org>/memberships/", MembershipsView.as_view()),
    path("<uuid:org>/memberships/<uuid:member>/", MembershipView.as_view()),
    path("<uuid:org>/transfer-owner/", TransferOwnerView.as_view()),
]
