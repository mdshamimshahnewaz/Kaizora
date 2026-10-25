import pytest
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


@pytest.fixture
def setup_roles(django_user_model):
    from modules.organizations.interfaces import create_organization

    operator = django_user_model.objects.create_superuser(username="operator", password="test")
    owner = django_user_model.objects.create_user(username="owner")
    worker = django_user_model.objects.create_user(username="worker")
    org = create_organization(operator.id, "Roles test", "UTC", owner.id)
    client = APIClient()
    client.force_authenticate(owner)
    return client, f"/api/v1/organizations/{org.id}/", owner, worker, operator


def test_live_grant_revoke_and_default_deny(setup_roles):
    client, base, owner, worker, operator = setup_roles
    response = client.get(base + "permissions/me/")
    assert response.status_code == 200
    assert "roles.manage" in response.json()["permissions"]
    member = client.post(base + "memberships/", {"user_id": str(worker.id)}, format="json")
    assert member.status_code == 201
    role = client.post(
        base + "roles/", {"name": "Reader", "permissions": ["memberships.read"]}, format="json"
    )
    assert role.status_code == 201
    grant = client.post(
        base + "role-assignments/",
        {
            "membership_id": member.json()["id"],
            "role_id": role.json()["id"],
            "reason": "Read access",
        },
        format="json",
    )
    assert grant.status_code == 201
    client.force_authenticate(worker)
    assert client.get(base + "memberships/").status_code == 200
    assert client.get(base + "roles/").status_code == 403
    client.force_authenticate(owner)
    assert (
        client.post(
            base + f"role-assignments/{grant.json()['id']}/revoke/",
            {"version": 1, "reason": "Access ended"},
            format="json",
        ).status_code
        == 200
    )
    client.force_authenticate(worker)
    assert client.get(base + "memberships/").status_code == 403
    client.force_authenticate(operator)
    assert client.get(base + "permissions/me/").status_code == 404


def post(client, base, path, body):
    return client.post(base + path, body, format="json")


def grant(client, base, worker, keys):
    membership = post(client, base, "memberships/", {"username": worker.username}).json()
    role = post(client, base, "roles/", {"name": "Custom", "permissions": keys}).json()
    assignment = post(
        client,
        base,
        "role-assignments/",
        {"membership_id": membership["id"], "role_id": role["id"], "reason": "Assigned"},
    ).json()
    return membership, role, assignment


def test_delegation_scope_and_strict_validation(setup_roles, django_user_model):
    from modules.organizations.interfaces import create_organization

    client, base, owner, worker, operator = setup_roles
    member, role, assignment = grant(
        client, base, worker, ["roles.manage", "roles.assign", "roles.read"]
    )
    admin_role = post(
        client, base, "roles/", {"name": "Admin", "permissions": ["memberships.manage"]}
    ).json()
    client.force_authenticate(worker)
    assert (
        post(
            client, base, "roles/", {"name": "Escalate", "permissions": ["memberships.manage"]}
        ).status_code
        == 403
    )
    assert (
        post(
            client,
            base,
            "role-assignments/",
            {"membership_id": member["id"], "role_id": admin_role["id"], "reason": "Self grant"},
        ).status_code
        == 403
    )
    assert (
        client.patch(
            base + f"roles/{admin_role['id']}/",
            {"version": 1, "reason": "Archive higher role", "status": "archived"},
            format="json",
        ).status_code
        == 403
    )
    assert (
        post(
            client, base, "roles/", {"name": "Reserved", "permissions": ["ownership.transfer"]}
        ).status_code
        == 400
    )
    assert (
        post(
            client, base, "roles/", {"name": "Forged", "permissions": [], "is_owner": True}
        ).status_code
        == 400
    )
    client.force_authenticate(owner)
    other = create_organization(operator.id, "Other", "UTC", owner.id)
    foreign_base = f"/api/v1/organizations/{other.id}/"
    foreign_member = post(client, foreign_base, "memberships/", {"user_id": str(worker.id)}).json()
    assert (
        post(
            client,
            base,
            "role-assignments/",
            {
                "membership_id": foreign_member["id"],
                "role_id": role["id"],
                "reason": "Wrong tenant",
            },
        ).status_code
        == 404
    )
    foreign_role = post(
        client, foreign_base, "roles/", {"name": "Foreign", "permissions": []}
    ).json()
    assert (
        post(
            client,
            base,
            "role-assignments/",
            {
                "membership_id": member["id"],
                "role_id": foreign_role["id"],
                "reason": "Wrong tenant",
            },
        ).status_code
        == 404
    )
    assert post(client, base, "roles/", {"name": "custom", "permissions": []}).status_code == 409
    assert (
        post(
            client,
            base,
            "roles/",
            {"name": "Invalid project", "scope_kind": "project", "permissions": ["roles.manage"]},
        ).status_code
        == 400
    )
    assert client.get(base + "roles/?page_size=101").status_code == 400
    assert client.get(base + "roles/?unexpected=true").status_code == 400
    assert client.get(base + "roles/?page=1&page=2").status_code == 400


def test_archive_suspension_history_and_role_conflict(setup_roles):
    from modules.identity.models import GrantChangeEvent, RoleAssignment

    client, base, owner, worker, operator = setup_roles
    member, role, assignment = grant(client, base, worker, ["memberships.read"])
    url = base + f"roles/{role['id']}/"
    assert (
        client.patch(
            url, {"version": 1, "reason": "Retire", "status": "archived"}, format="json"
        ).status_code
        == 200
    )
    assert (
        client.patch(
            url, {"version": 1, "reason": "Stale", "permissions": ["roles.manage"]}, format="json"
        ).status_code
        == 409
    )
    client.force_authenticate(worker)
    assert client.get(base + "permissions/me/").json()["permissions"] == []
    assert client.get(base + "memberships/").status_code == 403
    client.force_authenticate(owner)
    assert (
        client.patch(
            url, {"version": 2, "reason": "Restore", "status": "active"}, format="json"
        ).status_code
        == 200
    )
    member_url = base + f"memberships/{member['id']}/"
    assert (
        client.patch(
            member_url, {"version": 1, "status": "suspended", "reason": "Paused"}, format="json"
        ).status_code
        == 200
    )
    client.force_authenticate(worker)
    assert client.get(base + "permissions/me/").status_code == 404
    client.force_authenticate(owner)
    assert (
        client.patch(
            member_url, {"version": 2, "status": "active", "reason": "Returned"}, format="json"
        ).status_code
        == 200
    )
    client.force_authenticate(worker)
    assert client.get(base + "permissions/me/").json()["permissions"] == ["memberships.read"]
    assert RoleAssignment.objects.filter(pk=assignment["id"], ended_at__isnull=True).exists()
    assert GrantChangeEvent.objects.filter(role_id=role["id"]).count() == 4


def test_role_event_failure_rolls_back(setup_roles, monkeypatch):
    from modules.identity.models import GrantChangeEvent, OrganizationRole

    client, base, owner, worker, operator = setup_roles

    def fail(**kwargs):
        raise RuntimeError("Audit unavailable")

    monkeypatch.setattr(GrantChangeEvent.objects, "create", fail)
    with pytest.raises(RuntimeError):
        post(client, base, "roles/", {"name": "Atomic", "permissions": ["memberships.read"]})
    assert not OrganizationRole.objects.filter(name="Atomic").exists()


PROJECT_RESULT = None


def project_resolver(actor_id, organization_id, project_id):
    return PROJECT_RESULT


def test_project_context_requires_trusted_resolution(setup_roles, settings):
    from uuid import UUID, uuid4

    from rest_framework.exceptions import PermissionDenied

    import tests.test_roles as adapter
    from modules.identity.interfaces import ProjectScopeDTO, authorize
    from modules.organizations.interfaces import resolve_scope

    client, base, owner, worker, operator = setup_roles
    member = post(client, base, "memberships/", {"user_id": str(worker.id)}).json()
    role = post(
        client,
        base,
        "roles/",
        {"name": "Project manager", "scope_kind": "project", "permissions": ["projects.read"]},
    ).json()
    org_id = UUID(base.split("/")[-2])
    project_id = uuid4()
    scope = resolve_scope(worker.id, org_id)
    settings.IDENTITY_PROJECT_SCOPE_RESOLVER = None
    for context in [None, project_id, {"permissions": ["projects.read"]}]:
        with pytest.raises(PermissionDenied):
            authorize(scope, "projects.read", context)
    settings.IDENTITY_PROJECT_SCOPE_RESOLVER = "tests.test_roles.project_resolver"
    adapter.PROJECT_RESULT = ProjectScopeDTO(
        org_id, project_id, UUID(member["id"]), (UUID(role["id"]),)
    )
    authorize(scope, "projects.read", project_id)
    with pytest.raises(PermissionDenied):
        authorize(scope, "roles.manage", project_id)
    with pytest.raises(PermissionDenied):
        authorize(scope, "projects.read", uuid4())
    assert (
        post(
            client,
            base,
            "role-assignments/",
            {
                "membership_id": member["id"],
                "role_id": role["id"],
                "reason": "Project cannot be organization grant",
            },
        ).status_code
        == 409
    )
    client.patch(
        base + f"roles/{role['id']}/",
        {"version": 1, "reason": "Archive", "status": "archived"},
        format="json",
    )
    with pytest.raises(PermissionDenied):
        authorize(scope, "projects.read", project_id)
    adapter.PROJECT_RESULT = None


@pytest.mark.django_db(transaction=True)
def test_concurrent_role_updates_have_one_winner(setup_roles):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from uuid import UUID

    from django.db import close_old_connections

    from common.api import Conflict
    from modules.identity.interfaces import update_role

    client, base, owner, worker, operator = setup_roles
    role = post(client, base, "roles/", {"name": "Race", "permissions": []}).json()
    org_id = UUID(base.split("/")[-2])
    barrier = Barrier(2)

    def edit(key):
        close_old_connections()
        try:
            barrier.wait(timeout=5)
            try:
                update_role(
                    owner.id, org_id, UUID(role["id"]), 1, "Concurrent edit", permissions=[key]
                )
                return 200
            except Conflict:
                return 409
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(edit, ["memberships.read", "roles.read"]))
    assert sorted(results) == [200, 409]
    roles = client.get(base + "roles/").json()["results"]
    assert roles[0]["version"] == 2 and len(roles[0]["permissions"]) == 1


def test_operator_provisioning_by_username_preserves_access_boundary(setup_roles):
    from django.core.management import call_command
    from django.core.management.base import CommandError

    from modules.organizations.models import Membership, Organization

    client, base, owner, worker, operator = setup_roles
    call_command(
        "provision_organization",
        actor_username=operator.username,
        owner_username=worker.username,
        name="Provisioned",
        timezone="UTC",
    )
    organization = Organization.objects.get(name="Provisioned")
    assert (
        Membership.objects.filter(organization=organization, user=worker, is_owner=True).count()
        == 1
    )
    assert not Membership.objects.filter(organization=organization, user=operator).exists()
    with pytest.raises(CommandError):
        call_command(
            "provision_organization",
            actor_username=worker.username,
            owner_username=worker.username,
            name="Forbidden",
        )
    assert not Organization.objects.filter(name="Forbidden").exists()
