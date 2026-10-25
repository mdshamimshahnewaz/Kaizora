import pytest
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


@pytest.fixture
def setup(django_user_model):
    from modules.organizations.interfaces import create_organization

    user = django_user_model.objects.create_superuser(username="people-owner", password="test")
    org = create_organization(user.pk, "People", "UTC", user.pk)
    api = APIClient()
    api.force_authenticate(user)
    return user, org, api


def test_people_identity_and_intervals(setup, django_user_model):
    from datetime import timedelta

    from django.utils import timezone

    from modules.organizations.interfaces import list_memberships

    user, org, api = setup
    base = f"/api/v1/organizations/{org.id}/"
    count = django_user_model.objects.count()
    response = api.post(base + "resources/", {"code": "P1", "display_name": "Person"})
    assert response.status_code == 201, response.data
    person = response.data
    assert django_user_model.objects.count() == count
    assert api.post(base + "resources/", {"code": "p1", "display_name": "Other"}).status_code == 409
    member = list_memberships(user.pk, org.id).results[0]
    links = base + f"resources/{person['id']}/identity-links/"
    linked = api.post(
        links, {"membership_id": str(member.id), "version": 1, "reason": "Link account"}
    )
    assert linked.status_code == 201, linked.data
    assert (
        api.post(
            links, {"membership_id": str(member.id), "version": 2, "reason": "Again"}
        ).status_code
        == 409
    )
    assert (
        api.post(
            links + linked.data["id"] + "/end/", {"version": 2, "reason": "Unlink"}
        ).status_code
        == 200
    )
    assert api.get(links).data["count"] == 1
    team = api.post(base + "teams/", {"code": "T1", "name": "Delivery"}).data
    memberships = base + f"teams/{team['id']}/memberships/"
    today = timezone.now().date()
    end = today + timedelta(days=2)
    interval = {"resource_id": person["id"], "start_date": str(today), "end_date": str(end)}
    assignment = api.post(memberships, interval)
    assert assignment.status_code == 201, assignment.data
    assert api.post(memberships, interval).status_code == 409
    assert api.get(memberships + "?as_of=" + str(today)).data["count"] == 1
    assert api.get(memberships + "?as_of=" + str(end)).data["count"] == 0
    assert (
        api.patch(
            base + f"resources/{person['id']}/",
            {"status": "retired", "version": 3, "reason": "Left"},
        ).status_code
        == 200
    )
    assert (
        api.post(
            memberships,
            {**interval, "start_date": str(end), "end_date": str(end + timedelta(days=1))},
        ).status_code
        == 409
    )
    assert api.get(memberships).data["results"][0]["resource_status"] == "retired"


def test_scope_permissions_and_date_history(setup, django_user_model):
    from datetime import timedelta

    from django.utils import timezone

    from modules.identity.interfaces import assign_role, create_role
    from modules.organizations.interfaces import add_membership, create_organization
    from modules.resources.models import ResourceChangeEvent

    owner, org, api = setup
    base = f"/api/v1/organizations/{org.id}/"
    person = api.post(base + "resources/", {"code": "A", "display_name": "Person"}).data
    team = api.post(base + "teams/", {"code": "A", "name": "Team"}).data
    path = base + f"teams/{team['id']}/memberships/"
    today = timezone.now().date()
    assert (
        api.post(
            path, {"resource_id": person["id"], "start_date": str(today - timedelta(days=1))}
        ).status_code
        == 400
    )
    assignment = api.post(path, {"resource_id": person["id"], "start_date": str(today)}).data
    end = str(today + timedelta(days=1))
    assert (
        api.patch(
            path + assignment["id"] + "/", {"end_date": end, "version": 1, "reason": "Change"}
        ).status_code
        == 200
    )
    events = ResourceChangeEvent.objects.count()
    assert (
        api.patch(
            path + assignment["id"] + "/", {"end_date": end, "version": 1, "reason": "Stale"}
        ).status_code
        == 409
    )
    assert ResourceChangeEvent.objects.count() == events
    assert (
        api.patch(
            base + f"teams/{team['id']}/",
            {"status": "archived", "version": 1, "reason": "Ended team"},
        ).status_code
        == 200
    )
    assert (
        api.post(
            path, {"resource_id": person["id"], "start_date": str(today + timedelta(days=2))}
        ).status_code
        == 409
    )
    assert api.get(path).data["count"] == 1
    assert api.get(base + "resources/?email=a").status_code == 400
    assert api.get(base + "resources/?page_size=101").status_code == 400
    assert (
        api.patch(
            base + f"resources/{person['id']}/", {"code": "B", "version": 1, "reason": "Code"}
        ).status_code
        == 400
    )
    reader = django_user_model.objects.create_user(username="people-reader")
    member = add_membership(owner.pk, org.id, reader.pk)
    role = create_role(
        owner.pk,
        org.id,
        name="Reader",
        scope_kind="organization",
        permissions=["resources.read", "teams.read"],
    )
    assign_role(owner.pk, org.id, member.id, role.id, "Read")
    api.force_authenticate(reader)
    assert api.get(base + "resources/").status_code == 200
    assert set(api.get(base + f"resources/{person['id']}/").data) == {
        "id",
        "code",
        "display_name",
        "status",
        "version",
        "linked_membership_id",
    }
    assert api.post(base + "resources/", {"code": "B", "display_name": "Denied"}).status_code == 403
    assert (
        api.post(
            base + f"resources/{person['id']}/identity-links/",
            {"membership_id": str(member.id), "version": 1, "reason": "Denied"},
        ).status_code
        == 403
    )
    other = create_organization(owner.pk, "Other", "UTC", owner.pk)
    assert api.get(f"/api/v1/organizations/{other.id}/resources/").status_code == 404


def test_admin_people_team_link_and_assignment_commands(setup):
    from datetime import timedelta

    from django.test import Client
    from django.utils import timezone

    from modules.organizations.interfaces import list_memberships
    from modules.resources.models import Resource, ResourceIdentityLink, Team, TeamMembership

    owner, org, _ = setup
    browser = Client()
    browser.force_login(owner)
    assert (
        browser.post(
            "/admin/resources/resource/add/",
            {"organization": str(org.id), "code": "ADMIN", "name": "Admin person"},
        ).status_code
        == 302
    )
    assert (
        browser.post(
            "/admin/resources/team/add/",
            {"organization": str(org.id), "code": "ADMIN", "name": "Admin team"},
        ).status_code
        == 302
    )
    person = Resource.objects.get(code="ADMIN")
    team = Team.objects.get(code="ADMIN")
    form = browser.get("/admin/resources/resourceidentitylink/add/").context["form"]
    member = list_memberships(owner.pk, org.id).results[0]
    assert (
        browser.post(
            "/admin/resources/resourceidentitylink/add/",
            {
                "resource": str(person.id),
                "membership_id": str(member.id),
                "revisions": form.fields["revisions"].initial,
                "reason": "Link account",
            },
        ).status_code
        == 302
    )
    link = ResourceIdentityLink.objects.get(resource=person)
    assert (
        browser.post(
            f"/admin/resources/resourceidentitylink/{link.id}/change/",
            {"version": 2, "reason": "End link"},
        ).status_code
        == 302
    )
    link.refresh_from_db()
    assert link.ended_at is not None
    today = timezone.now().date()
    data = {
        "team": str(team.id),
        "resource": str(person.id),
        "start_date": str(today),
        "end_date": "",
    }
    assert browser.post("/admin/resources/teammembership/add/", data).status_code == 302
    assert browser.post("/admin/resources/teammembership/add/", data).status_code == 200
    assert TeamMembership.objects.count() == 1
    assignment = TeamMembership.objects.get(team=team)
    assert (
        browser.post(
            f"/admin/resources/teammembership/{assignment.id}/change/",
            {"end_date": str(today + timedelta(days=1)), "version": 1, "reason": "Move team"},
        ).status_code
        == 302
    )
    assert (
        browser.post(
            f"/admin/resources/resource/{person.id}/change/",
            {"name": person.display_name, "status": "retired", "version": 3, "reason": "Left"},
        ).status_code
        == 302
    )
    person.refresh_from_db()
    assert person.status == "retired" and person.version == 4
    assert (
        browser.post(
            f"/admin/resources/resource/{person.id}/change/",
            {"name": "Stale", "status": "active", "version": 3, "reason": "Old form"},
        ).status_code
        == 200
    )
    person.refresh_from_db()
    assert person.status == "retired"


def test_link_uniqueness_suspension_and_cross_tenant_admin(setup, django_user_model):
    from django.test import Client

    from modules.identity.interfaces import assign_role, create_role
    from modules.organizations.interfaces import add_membership, create_organization
    from modules.resources.models import ResourceIdentityLink

    owner, org, api = setup
    base = f"/api/v1/organizations/{org.id}/"
    person = api.post(base + "resources/", {"code": "ONE", "display_name": "One"}).data
    other_person = api.post(base + "resources/", {"code": "TWO", "display_name": "Two"}).data
    member_user = django_user_model.objects.create_user(username="linked-user", is_staff=True)
    member = add_membership(owner.pk, org.id, member_user.pk)
    path = base + f"resources/{person['id']}/identity-links/"
    assert (
        api.post(
            path, {"membership_id": str(member.id), "version": 1, "reason": "Identity"}
        ).status_code
        == 201
    )
    assert (
        api.post(
            base + f"resources/{other_person['id']}/identity-links/",
            {"membership_id": str(member.id), "version": 1, "reason": "Duplicate identity"},
        ).status_code
        == 409
    )
    assert (
        api.patch(
            base + f"memberships/{member.id}/",
            {"status": "suspended", "version": 1, "reason": "Access ended"},
        ).status_code
        == 200
    )
    assert api.get(base + f"resources/{person['id']}/").data["linked_membership_id"] == str(
        member.id
    )
    assert ResourceIdentityLink.objects.get(resource_id=person["id"]).ended_at is None
    other_org = create_organization(owner.pk, "Other team", "UTC", owner.pk)
    other_base = f"/api/v1/organizations/{other_org.id}/"
    team = api.post(other_base + "teams/", {"code": "X", "name": "Other org team"}).data
    role = create_role(
        owner.pk,
        org.id,
        name="People manager",
        scope_kind="organization",
        permissions=["resources.read", "resources.manage", "teams.read", "teams.manage"],
    )
    # A separate active manager can use Admin only within the granted organization.
    manager = django_user_model.objects.create_user(username="people-manager", is_staff=True)
    manager_member = add_membership(owner.pk, org.id, manager.pk)
    assign_role(owner.pk, org.id, manager_member.id, role.id, "Manage people")
    browser = Client()
    browser.force_login(manager)
    response = browser.get("/admin/resources/team/")
    assert response.status_code == 200 and b"Other org team" not in response.content
    assert browser.post(
        f"/admin/resources/team/{team['id']}/change/",
        {"name": "Forged", "status": "archived", "version": 1, "reason": "Forged"},
    ).status_code in {302, 403, 404}
    assert api.get(other_base + f"teams/{team['id']}/").data["name"] == "Other org team"
