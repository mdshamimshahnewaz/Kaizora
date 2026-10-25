from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from modules.identity.interfaces import create_role
from modules.organizations.interfaces import add_membership, create_organization, resolve_scope
from modules.projects.interfaces import create_project
from modules.resources.interfaces import create_resource, create_team
from modules.resources.models import Resource, ResourceIdentityLink, TeamMembership

pytestmark = pytest.mark.django_db


@pytest.fixture
def setup(django_user_model):
    owner = django_user_model.objects.create_superuser(username="selection-owner", password="test")
    org = create_organization(owner.pk, "Selection", "UTC", owner.pk)
    user = django_user_model.objects.create_user(username="rahim", first_name="Rahim")
    member = add_membership(owner.pk, org.id, user.pk)
    scope = resolve_scope(owner.pk, org.id)
    role = create_role(
        owner.pk,
        org.id,
        "PM",
        ["projects.read", "projects.manage", "projects.access.manage"],
        "project",
    )
    project = create_project(
        scope,
        code="P",
        name="Project",
        type="delivery",
        initial_manager_membership_id=org.membership_id,
        initial_manager_role_id=role.id,
    )
    team = create_team(scope, "T", "Team")
    api = APIClient()
    api.force_authenticate(owner)
    return owner, org, user, member, scope, project, team, api


def test_direct_member_assignment_reuses_identity_and_rolls_back_invalid_dates(setup):
    _, org, _, member, _, _, team, api = setup
    url = f"/api/v1/organizations/{org.id}/teams/{team.id}/memberships/"
    today = timezone.now().date()
    body = {"membership_id": str(member.id), "start_date": str(today)}
    assert api.post(url, {**body, "start_date": str(today - timedelta(days=1))}).status_code == 400
    assert Resource.objects.count() == 0
    response = api.post(url, body)
    assert response.status_code == 201, response.data
    resource_id = response.data["resource_id"]
    assert Resource.objects.count() == ResourceIdentityLink.objects.count() == 1
    assert api.post(url, body).status_code == 409
    from_member = api.post(
        f"/api/v1/organizations/{org.id}/resources/from-member/", {"membership_id": str(member.id)}
    )
    assert from_member.status_code == 200
    assert from_member.data["id"] == resource_id
    assert Resource.objects.count() == 1
    assert api.post(url, {**body, "resource_id": resource_id}).status_code == 400


def test_search_scope_and_suspended_member_rejected(setup, django_user_model):
    owner, org, user, member, _, _, team, api = setup
    other = create_organization(owner.pk, "Other", "UTC", owner.pk)
    foreign = add_membership(owner.pk, other.id, user.pk)
    choices = (
        f"/api/v1/organizations/{org.id}/resources/choices/?kind=members&search=rahim&page_size=1"
    )
    result = api.get(choices)
    assert result.status_code == 200 and result.data["count"] == 1
    assert result.data["results"][0]["id"] == str(member.id)
    assert api.get(choices + "&page=2").status_code == 404
    url = f"/api/v1/organizations/{org.id}/teams/{team.id}/memberships/"
    body = {"membership_id": str(foreign.id), "start_date": str(timezone.now().date())}
    assert api.post(url, body).status_code in (400, 404)
    from modules.organizations.interfaces import change_membership

    change_membership(owner.pk, org.id, member.id, "suspended", 1, "Test")
    assert api.get(choices).data["count"] == 0
    assert api.post(url, {**body, "membership_id": str(member.id)}).status_code in (400, 404)
    api.force_authenticate(user)
    assert api.get(choices).status_code == 404
    assert Resource.objects.count() == 0


def test_no_login_and_member_workforce_history_without_access_grants(setup, django_user_model):
    owner, org, user, member, scope, project, _, api = setup
    from modules.projects.interfaces import transition_project
    from modules.projects.models import ProjectAccess, ProjectWorker

    count = django_user_model.objects.count()
    guest = create_resource(scope, "EXT", "External worker")
    url = f"/api/v1/organizations/{org.id}/projects/{project.id}/workforce/"
    row = api.post(url, {"resource_id": str(guest.id), "reason": "Contractor work"})
    assert row.status_code == 201, row.data
    assert api.post(url, {"resource_id": str(guest.id), "reason": "Duplicate"}).status_code == 409
    member_row = api.post(url, {"membership_id": str(member.id), "reason": "Delivery"})
    assert member_row.status_code == 201
    assert django_user_model.objects.count() == count
    assert ProjectAccess.objects.count() == 1  # Only initial manager, not workforce members.
    api.force_authenticate(user)
    assert api.get(url).status_code == 404
    api.force_authenticate(owner)
    end_url = url + row.data["id"] + "/end/"
    assert api.post(end_url, {"version": 2, "reason": "Stale"}).status_code == 409
    assert api.post(end_url, {"version": 1, "reason": "Finished"}).status_code == 200
    assert ProjectWorker.objects.get(pk=row.data["id"]).end_reason == "Finished"
    assert api.get(url).data["count"] == 2
    transition_project(scope, project.id, target_status="archived", version=1, reason="Stop")
    assert api.post(url, {"resource_id": str(guest.id), "reason": "Again"}).status_code == 409


def test_project_manager_without_org_resource_management_can_assign_but_reader_cannot(setup):
    owner, org, user, member, scope, project, _, api = setup
    from modules.projects.interfaces import grant_access

    role = create_role(
        owner.pk, org.id, "Delegated PM", ["projects.read", "projects.manage"], "project"
    )
    grant_access(scope, project.id, membership_id=member.id, role_id=role.id, reason="PM")
    api.force_authenticate(user)
    url = f"/api/v1/organizations/{org.id}/projects/{project.id}/workforce/"
    assert api.get(url + "options/?kind=members&search=rahim").data["count"] == 1
    assert api.post(url, {"membership_id": str(member.id), "reason": "Work"}).status_code == 201
    from modules.identity.interfaces import update_role

    update_role(owner.pk, org.id, role.id, 1, "Read only", permissions=["projects.read"])
    assert api.get(url).status_code == 200
    assert api.get(url + "options/?kind=members").status_code == 403
    assert (
        api.post(url, {"membership_id": str(org.membership_id), "reason": "No"}).status_code == 403
    )


def test_ended_link_never_silently_duplicates_identity(setup):
    _, org, _, member, scope, _, _, api = setup
    from modules.resources.interfaces import add_resource_from_member, end_identity_link

    person = add_resource_from_member(scope, member.id)
    link = ResourceIdentityLink.objects.get(resource_id=person.id)
    end_identity_link(scope, person.id, link.id, person.version, "Unlink")
    url = f"/api/v1/organizations/{org.id}/resources/from-member/"
    assert api.post(url, {"membership_id": str(member.id)}).status_code == 409
    assert Resource.objects.count() == 1


def test_admin_direct_member_and_no_login_roster_commands(setup, client):
    owner, org, _, member, scope, project, team, _ = setup
    from modules.projects.models import ProjectWorker

    client.force_login(owner)
    form = client.get("/admin/resources/resource/add/")
    assert b'data-searchable="true"' in form.content
    assert (
        client.post(
            "/admin/resources/resource/add/",
            {"organization": str(org.id), "membership_id": str(member.id), "code": "", "name": ""},
        ).status_code
        == 302
    )
    assert (
        client.post(
            "/admin/resources/teammembership/add/",
            {
                "team": str(team.id),
                "membership_id": str(member.id),
                "resource": "",
                "start_date": str(timezone.now().date()),
                "end_date": "",
            },
        ).status_code
        == 302
    )
    assert TeamMembership.objects.count() == 1
    guest = create_resource(scope, "GUEST", "Guest")
    assert (
        client.post(
            "/admin/projects/projectworker/add/",
            {
                "project": str(project.id),
                "membership_id": "",
                "resource_id": str(guest.id),
                "reason": "Work",
            },
        ).status_code
        == 302
    )
    row = ProjectWorker.objects.get()
    assert (
        client.post(
            f"/admin/projects/projectworker/{row.id}/change/", {"version": 1, "reason": "Complete"}
        ).status_code
        == 302
    )
    row.refresh_from_db()
    assert row.ended_at is not None


def test_name_only_resource_creates_no_login_and_retired_identity_is_not_duplicated(
    setup, django_user_model
):
    _, org, _, member, scope, project, _, api = setup
    from modules.resources.interfaces import add_resource_from_member, update_resource

    user_count = django_user_model.objects.count()
    created = api.post(
        f"/api/v1/organizations/{org.id}/resources/", {"display_name": "No login analyst"}
    )
    assert created.status_code == 201
    assert created.data["code"] and created.data["linked_membership_id"] is None
    assert django_user_model.objects.count() == user_count
    linked = add_resource_from_member(scope, member.id)
    update_resource(scope, linked.id, version=linked.version, reason="Retired", status="retired")
    url = f"/api/v1/organizations/{org.id}/projects/{project.id}/workforce/"
    assert api.post(url, {"membership_id": str(member.id), "reason": "Work"}).status_code == 409
    assert Resource.objects.count() == 2
