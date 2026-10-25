import pytest
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


def test_private_project_creation(django_user_model):
    from modules.identity.interfaces import create_role
    from modules.organizations.interfaces import create_organization

    owner = django_user_model.objects.create_superuser(username="project-owner", password="test")
    org = create_organization(owner.pk, "Projects", "UTC", owner.pk)
    role = create_role(
        owner.pk,
        org.id,
        "Project manager",
        [
            "projects.read",
            "projects.manage",
            "projects.access.manage",
            "projects.access.read",
            "projects.transition",
            "projects.reopen",
            "projects.restore",
        ],
        "project",
    )
    api = APIClient()
    api.force_authenticate(owner)
    response = api.post(
        f"/api/v1/organizations/{org.id}/projects/",
        {
            "code": "BUILD",
            "name": "Build",
            "type": "delivery",
            "initial_manager_membership_id": str(org.membership_id),
            "initial_manager_role_id": str(role.id),
        },
        format="json",
    )
    assert response.status_code == 201
    assert response.data["status"] == "draft"


@pytest.fixture
def project_setup(django_user_model):
    from modules.identity.interfaces import create_role
    from modules.organizations.interfaces import create_organization, resolve_scope
    from modules.projects.interfaces import create_project

    owner = django_user_model.objects.create_superuser(username="owner", password="test")
    org = create_organization(owner.pk, "Projects", "UTC", owner.pk)
    keys = [
        "projects.read",
        "projects.manage",
        "projects.access.manage",
        "projects.access.read",
        "projects.transition",
        "projects.reopen",
        "projects.restore",
    ]
    role = create_role(owner.pk, org.id, "Manager", keys, "project")
    scope = resolve_scope(owner.pk, org.id)
    project = create_project(
        scope,
        code="ONE",
        name="One",
        type="delivery",
        initial_manager_membership_id=org.membership_id,
        initial_manager_role_id=role.id,
    )
    api = APIClient()
    api.force_authenticate(owner)
    return owner, org, role, scope, project, api


def test_private_visibility_delegation_and_revocation(project_setup, django_user_model):
    from modules.identity.interfaces import assign_role, create_role, update_role
    from modules.organizations.interfaces import add_membership, change_membership
    from modules.projects.interfaces import end_access, grant_access
    from modules.projects.models import ProjectAccess

    owner, org, manager, scope, project, api = project_setup
    base = f"/api/v1/organizations/{org.id}/projects/"
    user = django_user_model.objects.create_user(username="reader")
    member = add_membership(owner.pk, org.id, user.pk)
    role = create_role(owner.pk, org.id, "Reader", ["projects.read"], "project")
    api.force_authenticate(user)
    assert api.get(base).data["count"] == 0
    assert api.get(base + str(project.id) + "/").status_code == 404
    grant = grant_access(scope, project.id, membership_id=member.id, role_id=role.id, reason="Read")
    assert api.get(base).data["count"] == 1
    assert api.get(base + str(project.id) + "/").data["capabilities"] == ["projects.read"]
    assert (
        api.post(
            base + str(project.id) + "/access/",
            {"membership_id": str(member.id), "role_id": str(manager.id), "reason": "Escalate"},
        ).status_code
        == 403
    )
    update_role(owner.pk, org.id, role.id, 1, "Archive", status="archived")
    assert api.get(base).data["count"] == 0
    assert api.get(base + str(project.id) + "/").status_code == 404
    update_role(owner.pk, org.id, role.id, 2, "Restore", status="active")
    change_membership(owner.pk, org.id, member.id, "suspended", 1, "Leave")
    assert api.get(base).status_code == 404
    change_membership(owner.pk, org.id, member.id, "active", 2, "Return")
    end_access(scope, project.id, grant.id, version=1, reason="Access ended")
    assert api.get(base).data["count"] == 0
    assert ProjectAccess.objects.get(pk=grant.id).ended_at is not None
    # Organization-wide read permits visibility but does not imply management.
    reader_all = create_role(owner.pk, org.id, "All reader", ["projects.read_all"])
    assign_role(owner.pk, org.id, member.id, reader_all.id, "Overview")
    assert api.get(base).data["count"] == 1
    assert (
        api.patch(
            base + str(project.id) + "/", {"name": "No", "version": 1, "reason": "No"}
        ).status_code
        == 403
    )


def test_creation_rollback_clients_and_lifecycle(project_setup, django_user_model):
    from modules.clients.interfaces import create_client, update_client
    from modules.identity.interfaces import assign_role, create_role
    from modules.organizations.interfaces import add_membership, create_organization
    from modules.projects.models import Project, ProjectAccess, ProjectChangeEvent

    owner, org, manager, scope, project, api = project_setup
    base = f"/api/v1/organizations/{org.id}/projects/"
    body = {
        "code": "OPS",
        "name": "Operations",
        "type": "operations",
        "initial_manager_membership_id": str(org.membership_id),
        "initial_manager_role_id": str(manager.id),
    }
    client = create_client(scope, "ACME", "Acme")
    body["client_id"] = str(client.id)
    assert api.post(base, body, format="json").status_code == 201
    assert api.post(base, {**body, "code": "ops"}, format="json").status_code == 409
    update_client(scope, client.id, version=1, reason="Archive", status="archived")
    assert api.post(base, {**body, "code": "NEW"}, format="json").status_code == 409
    assert Project.objects.count() == 2 and ProjectAccess.objects.count() == 2
    other = create_organization(owner.pk, "Other", "UTC", owner.pk)
    assert (
        api.post(
            base,
            {
                **body,
                "code": "CROSS",
                "client_id": None,
                "initial_manager_membership_id": str(other.membership_id),
            },
            format="json",
        ).status_code
        == 404
    )
    user = django_user_model.objects.create_user(username="creator")
    member = add_membership(owner.pk, org.id, user.pk)
    role = create_role(owner.pk, org.id, "Creator", ["projects.create"])
    assign_role(owner.pk, org.id, member.id, role.id, "Create only")
    api.force_authenticate(user)
    assert (
        api.post(base, {**body, "code": "ESC", "client_id": None}, format="json").status_code == 403
    )
    assert api.get(base + "options/?kind=members").status_code == 200
    assert api.get(base + "options/?kind=roles").data["count"] == 0
    api.force_authenticate(owner)
    detail = base + str(project.id) + "/"
    assert (
        api.patch(detail, {"type": "operations", "version": 1, "reason": "No"}).status_code == 400
    )
    assert (
        api.patch(
            detail,
            {
                "start_date": "2026-10-20",
                "target_end_date": "2026-10-01",
                "version": 1,
                "reason": "Bad",
            },
        ).status_code
        == 400
    )
    assert (
        api.patch(detail, {"name": "Renamed", "version": 1, "reason": "Rename"}).status_code == 200
    )
    assert api.patch(detail, {"name": "Stale", "version": 1, "reason": "Old"}).status_code == 409
    for target, version in [("active", 2), ("completed", 3), ("active", 4), ("archived", 5)]:
        assert (
            api.post(
                detail + "transition/",
                {"target_status": target, "version": version, "reason": "Lifecycle"},
            ).status_code
            == 200
        )
    assert api.patch(detail, {"name": "No", "version": 6, "reason": "Archived"}).status_code == 409
    assert (
        api.post(
            detail + "access/",
            {"membership_id": str(member.id), "role_id": str(manager.id), "reason": "Archived"},
        ).status_code
        == 409
    )
    assert (
        api.post(
            detail + "transition/", {"target_status": "active", "version": 6, "reason": "Invalid"}
        ).status_code
        == 409
    )
    assert (
        api.post(
            detail + "transition/", {"target_status": "draft", "version": 6, "reason": "Restore"}
        ).status_code
        == 200
    )
    assert ProjectChangeEvent.objects.filter(project_id=project.id).count() == 8
    assert api.get(base + "?unknown=1").status_code == 400
    assert api.get(base + "?page_size=101").status_code == 400
    assert api.get(base + "?client_id=bad").status_code == 400


def test_admin_project_commands_and_history(project_setup, django_user_model):
    from django.test import Client

    from modules.organizations.interfaces import add_membership
    from modules.projects.models import Project, ProjectAccess

    owner, org, role, scope, project, _ = project_setup
    browser = Client()
    browser.force_login(owner)
    response = browser.post(
        "/admin/projects/project/add/",
        {
            "organization": str(org.id),
            "code": "ADMIN",
            "name": "Admin project",
            "type": "delivery",
            "initial_manager_membership_id": str(org.membership_id),
            "initial_manager_role_id": str(role.id),
            "client_id": "",
            "description": "",
            "start_date": "",
            "target_end_date": "",
        },
    )
    assert response.status_code == 302
    created = Project.objects.get(code="ADMIN")
    assert (
        browser.post(
            f"/admin/projects/project/{created.id}/change/",
            {"action": "active", "version": 1, "reason": "Start"},
        ).status_code
        == 302
    )
    assert (
        browser.post(
            f"/admin/projects/project/{created.id}/change/",
            {"action": "archived", "version": 1, "reason": "Stale"},
        ).status_code
        == 200
    )
    created.refresh_from_db()
    assert created.status == "active" and created.version == 2
    user = django_user_model.objects.create_user(username="admin-target")
    member = add_membership(owner.pk, org.id, user.pk)
    response = browser.post(
        "/admin/projects/projectaccess/add/",
        {
            "project": str(created.id),
            "membership_id": str(member.id),
            "role_id": str(role.id),
            "reason": "Manager",
        },
    )
    assert response.status_code == 302
    grant = ProjectAccess.objects.get(project=created, membership_id=member.id)
    assert (
        browser.post(
            f"/admin/projects/projectaccess/{grant.id}/change/", {"version": 1, "reason": "End"}
        ).status_code
        == 302
    )
    grant.refresh_from_db()
    assert grant.ended_at is not None
    assert (
        browser.post(f"/admin/projects/project/{created.id}/delete/", {"post": "yes"}).status_code
        == 403
    )


def test_project_list_query_count_is_bounded(project_setup, django_assert_num_queries):
    from django.db import connection
    from django.test.utils import CaptureQueriesContext

    from modules.projects.models import Project

    owner, org, role, scope, project, api = project_setup
    base = f"/api/v1/organizations/{org.id}/projects/"
    with CaptureQueriesContext(connection) as one:
        assert api.get(base).status_code == 200
    Project.objects.bulk_create(
        [
            Project(
                organization_id=org.id,
                code=f"P{i}",
                normalized_code=f"p{i}",
                name=f"Project {i}",
                type="delivery",
            )
            for i in range(49)
        ]
    )
    with CaptureQueriesContext(connection) as fifty:
        response = api.get(base)
        assert response.status_code == 200 and len(response.data["results"]) == 50
    assert len(fifty) <= len(one) + 2
    assert len(fifty) <= 20
