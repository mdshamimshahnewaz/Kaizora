import pytest
from django.test import Client
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


def test_admin_creates_and_manages_through_domain_commands(django_user_model):
    from modules.identity.models import GrantChangeEvent, OrganizationRole, RoleAssignment
    from modules.organizations.models import Membership, MembershipStatusEvent, Organization

    operator = django_user_model.objects.create_superuser(username="admin", password="test")
    worker = django_user_model.objects.create_user(username="worker")
    client = Client()
    client.force_login(operator)
    response = client.post(
        "/admin/organizations/organization/add/",
        {"name": "UI org", "timezone": "UTC", "owner_username": "admin"},
    )
    assert response.status_code == 302
    org = Organization.objects.get(name="UI org")
    assert (
        client.post(
            "/admin/organizations/membership/add/", {"organization": org.pk, "username": "worker"}
        ).status_code
        == 302
    )
    member = Membership.objects.get(organization=org, user=worker)
    assert (
        client.post(
            "/admin/identity/organizationrole/add/",
            {
                "organization": org.pk,
                "name": "Reader",
                "scope_kind": "organization",
                "permissions": ["memberships.read"],
            },
        ).status_code
        == 302
    )
    role = OrganizationRole.objects.get(name="Reader")
    assert (
        client.post(
            "/admin/identity/roleassignment/add/",
            {
                "organization": org.pk,
                "membership_id": member.pk,
                "role_id": role.pk,
                "reason": "Support",
            },
        ).status_code
        == 302
    )
    assignment = RoleAssignment.objects.get(role=role)
    role_url = f"/admin/identity/organizationrole/{role.pk}/change/"
    assert (
        client.post(
            role_url,
            {
                "name": "Reader",
                "permissions": ["memberships.read"],
                "status": "archived",
                "version": 1,
                "reason": "Archive",
            },
        ).status_code
        == 302
    )
    stale = client.post(
        role_url,
        {
            "name": "Overwrite",
            "permissions": [],
            "status": "active",
            "version": 1,
            "reason": "Stale",
        },
    )
    assert stale.status_code == 200 and b"This record changed" in stale.content
    role.refresh_from_db()
    assert role.name == "Reader" and role.version == 2
    assert (
        client.post(
            f"/admin/identity/roleassignment/{assignment.pk}/change/",
            {"version": 1, "reason": "Revoke"},
        ).status_code
        == 302
    )
    assignment.refresh_from_db()
    assert assignment.ended_at is not None
    assert (
        client.post(
            f"/admin/organizations/membership/{member.pk}/change/",
            {"status": "suspended", "version": 1, "reason": "Pause"},
        ).status_code
        == 302
    )
    assert MembershipStatusEvent.objects.filter(membership=member).count() == 2
    assert GrantChangeEvent.objects.filter(role=role).count() == 4
    assert (
        client.post(
            f"/admin/organizations/membership/{member.pk}/change/",
            {"status": "active", "version": 2, "reason": "Return"},
        ).status_code
        == 302
    )
    assert (
        client.post(
            f"/admin/organizations/organization/{org.pk}/change/",
            {"target_membership_id": member.pk, "version": 1, "reason": "New owner"},
        ).status_code
        == 302
    )
    member.refresh_from_db()
    assert member.is_owner


def test_admin_no_business_bypass_and_csrf(django_user_model):
    from modules.organizations.interfaces import create_organization

    operator = django_user_model.objects.create_superuser(username="operator", password="test")
    owner = django_user_model.objects.create_user(username="owner")
    org = create_organization(operator.pk, "Foreign", "UTC", owner.pk)
    client = Client()
    client.force_login(operator)
    assert (
        client.post(
            "/admin/organizations/membership/add/", {"organization": org.id, "username": "operator"}
        ).status_code
        == 403
    )
    assert (
        client.post(
            "/admin/identity/organizationrole/add/",
            {
                "organization": org.id,
                "name": "Bypass",
                "scope_kind": "organization",
                "permissions": [],
            },
        ).status_code
        == 403
    )
    csrf_client = Client(enforce_csrf_checks=True)
    csrf_client.force_login(operator)
    assert (
        csrf_client.post(
            "/admin/organizations/organization/add/",
            {"name": "Blocked", "timezone": "UTC", "owner_username": "operator"},
        ).status_code
        == 403
    )


def test_frontend_provisioning_capability_and_exact_owner(django_user_model):
    operator = django_user_model.objects.create_superuser(username="operator", password="test")
    owner = django_user_model.objects.create_user(username="owner")
    client = APIClient()
    client.force_authenticate(owner)
    assert client.get("/api/v1/organizations/provisioning/").json() == {"can_create": False}
    assert (
        client.post(
            "/api/v1/organizations/",
            {"name": "Denied", "timezone": "UTC", "owner_username": "owner"},
            format="json",
        ).status_code
        == 403
    )
    client.force_authenticate(operator)
    assert client.get("/api/v1/organizations/provisioning/").json() == {"can_create": True}
    response = client.post(
        "/api/v1/organizations/",
        {"name": "Created", "timezone": "UTC", "owner_username": "owner"},
        format="json",
    )
    assert response.status_code == 201
    assert response.json()["membership_id"] is None
    assert client.get(f"/api/v1/organizations/{response.json()['id']}/").status_code == 404
