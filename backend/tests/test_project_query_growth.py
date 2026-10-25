import pytest
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework.test import APIClient

from modules.identity.interfaces import create_role
from modules.organizations.interfaces import create_organization, resolve_scope
from modules.projects.interfaces import create_project
from modules.projects.models import Project, ProjectAccess

pytestmark = pytest.mark.django_db


@pytest.fixture
def project_data(django_user_model):
    owner = django_user_model.objects.create_superuser(username="query-owner", password="test")
    org = create_organization(owner.pk, "Query check", "UTC", owner.pk)
    role = create_role(
        owner.pk,
        org.id,
        "Manager",
        ["projects.read", "projects.manage", "projects.access.read", "projects.access.manage"],
        "project",
    )
    project = create_project(
        resolve_scope(owner.pk, org.id),
        code="ONE",
        name="One",
        type="delivery",
        initial_manager_membership_id=org.membership_id,
        initial_manager_role_id=role.id,
    )
    return owner, org, role, project


def test_access_history_queries_do_not_grow_per_row(project_data):
    owner, org, role, project = project_data
    api = APIClient()
    api.force_authenticate(owner)
    url = f"/api/v1/organizations/{org.id}/projects/{project.id}/access/"
    with CaptureQueriesContext(connection) as one:
        assert api.get(url).status_code == 200
    ProjectAccess.objects.bulk_create(
        [
            ProjectAccess(
                organization_id=org.id,
                project_id=project.id,
                membership_id=org.membership_id,
                role_id=role.id,
                ended_at=timezone.now(),
            )
            for _ in range(49)
        ]
    )
    with CaptureQueriesContext(connection) as fifty:
        response = api.get(url)
        assert response.status_code == 200 and len(response.data["results"]) == 50
    assert len(fifty) <= len(one) + 2


def test_admin_grant_list_queries_do_not_grow_per_project(project_data):
    owner, org, role, project = project_data
    browser = Client()
    browser.force_login(owner)
    url = "/admin/projects/projectaccess/"
    with CaptureQueriesContext(connection) as one:
        assert browser.get(url).status_code == 200
    projects = [
        Project(
            organization_id=org.id,
            code=f"C{i}",
            normalized_code=f"c{i}",
            name=f"Client project {i}",
            type="delivery",
        )
        for i in range(49)
    ]
    Project.objects.bulk_create(projects)
    ProjectAccess.objects.bulk_create(
        [
            ProjectAccess(
                organization_id=org.id, project=p, membership_id=org.membership_id, role_id=role.id
            )
            for p in projects
        ]
    )
    with CaptureQueriesContext(connection) as fifty:
        assert browser.get(url).status_code == 200
    assert len(fifty) <= len(one) + 10


def test_admin_capability_batch_matches_live_private_access(project_data, django_user_model):
    from modules.identity.interfaces import update_role
    from modules.organizations.interfaces import add_membership
    from modules.projects.interfaces import (
        get_admin_project_capabilities,
        get_project,
        grant_access,
    )

    owner, org, role, project = project_data
    reader = django_user_model.objects.create_user(username="private-reader")
    member = add_membership(owner.pk, org.id, reader.pk)
    scope = resolve_scope(reader.pk, org.id)
    assert get_admin_project_capabilities(scope) == ()
    read_role = create_role(owner.pk, org.id, "Reader", ["projects.read"], "project")
    grant_access(
        resolve_scope(owner.pk, org.id),
        project.id,
        membership_id=member.id,
        role_id=read_role.id,
        reason="Read",
    )
    batch = get_admin_project_capabilities(scope)
    assert len(batch) == 1 and batch[0].id == project.id
    assert (
        set(batch[0].capabilities)
        == set(get_project(scope, project.id).capabilities)
        == {"projects.read"}
    )
    update_role(owner.pk, org.id, read_role.id, 1, "Archive role", status="archived")
    assert get_admin_project_capabilities(scope) == ()
