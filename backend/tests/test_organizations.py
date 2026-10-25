import pytest
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


def test_bootstrap_and_scope(django_user_model):
    owner = django_user_model.objects.create_user(username="org-owner")
    operator = django_user_model.objects.create_superuser(username="operator", password="test")
    client = APIClient()
    client.force_authenticate(operator)
    response = client.post(
        "/api/v1/organizations/",
        {"name": "Example", "timezone": "Asia/Dhaka", "owner_user_id": str(owner.id)},
        format="json",
    )
    assert response.status_code == 201
    org = response.json()
    assert client.get(f"/api/v1/organizations/{org['id']}/").status_code == 404
    client.force_authenticate(owner)
    assert client.get("/api/v1/organizations/").json()["count"] == 1
    assert client.get(f"/api/v1/organizations/{org['id']}/").json()["is_owner"] is True
    assert (
        client.post(
            "/api/v1/organizations/",
            {"name": "Forbidden", "timezone": "UTC", "owner_user_id": str(owner.id)},
            format="json",
        ).status_code
        == 403
    )


def owner_policy(scope, permission):
    return scope.is_owner and permission in {"memberships.read", "memberships.manage"}


@pytest.fixture
def org_setup(django_user_model, settings):
    from modules.organizations.interfaces import create_organization

    settings.ORGANIZATIONS_PERMISSION_POLICY = "tests.test_organizations.owner_policy"
    operator = django_user_model.objects.create_superuser(username="operator", password="test")
    owner = django_user_model.objects.create_user(username="owner")
    member = django_user_model.objects.create_user(username="worker")
    outsider = django_user_model.objects.create_user(username="outsider", is_staff=True)
    org = create_organization(operator.id, "Organization A", "Asia/Dhaka", owner.id)
    client = APIClient()
    client.force_authenticate(owner)
    return client, org, owner, member, outsider, operator


def test_membership_history_reactivation_and_scope(org_setup):
    from rest_framework.exceptions import NotFound

    from modules.organizations.interfaces import resolve_scope
    from modules.organizations.models import MembershipStatusEvent

    client, org, owner, member, outsider, operator = org_setup
    path = f"/api/v1/organizations/{org.id}/memberships/"
    created = client.post(path, {"user_id": str(member.id)}, format="json")
    assert created.status_code == 201
    snapshot = created.json()
    stable_id = snapshot["id"]
    assert client.post(path, {"user_id": str(member.id)}, format="json").status_code == 409
    scope = resolve_scope(member.id, org.id)
    changed = client.patch(
        path + stable_id + "/",
        {"status": "ended", "version": 1, "reason": "Assignment access ended"},
        format="json",
    )
    assert changed.status_code == 200
    with pytest.raises(NotFound):
        resolve_scope(member.id, org.id)
    revived = client.patch(
        path + stable_id + "/",
        {"status": "active", "version": 2, "reason": "Rejoined"},
        format="json",
    )
    assert revived.json()["id"] == stable_id
    assert str(resolve_scope(member.id, org.id).membership_id) == stable_id
    events = list(
        MembershipStatusEvent.objects.filter(membership_id=scope.membership_id)
        .order_by("id")
        .values_list("before_status", "after_status")
    )
    assert events == [("", "active"), ("active", "ended"), ("ended", "active")]
    stale = client.patch(
        path + stable_id + "/",
        {"status": "suspended", "version": 1, "reason": "Stale"},
        format="json",
    )
    assert stale.status_code == 409
    assert MembershipStatusEvent.objects.filter(membership_id=stable_id).count() == 3
    client.force_authenticate(outsider)
    assert client.get(path).status_code == 404
    assert client.get("/api/v1/organizations/").json()["count"] == 0
    client.force_authenticate(member)
    assert client.get(path).status_code == 403


def test_default_policy_denies_management_even_owner(org_setup, settings):
    client, org, owner, member, *_ = org_setup
    settings.ORGANIZATIONS_PERMISSION_POLICY = None
    path = f"/api/v1/organizations/{org.id}/memberships/"
    assert client.get(path).status_code == 403
    assert client.post(path, {"user_id": str(member.id)}, format="json").status_code == 403
    assert client.get(f"/api/v1/organizations/{org.id}/").status_code == 200


def test_owner_transfer_atomic_and_last_owner_guard(org_setup):
    from modules.organizations.models import Membership, OrganizationChangeEvent

    client, org, owner, member, *_ = org_setup
    base = f"/api/v1/organizations/{org.id}/"
    source = Membership.objects.get(organization_id=org.id, user=owner)
    assert (
        client.patch(
            base + f"memberships/{source.id}/",
            {"status": "suspended", "version": 1, "reason": "Leave"},
            format="json",
        ).status_code
        == 409
    )
    target = client.post(base + "memberships/", {"user_id": str(member.id)}, format="json").json()
    moved = client.post(
        base + "transfer-owner/",
        {"target_membership_id": target["id"], "version": 1, "reason": "Handover"},
        format="json",
    )
    assert moved.status_code == 200
    assert moved.json()["is_owner"] is False
    source.refresh_from_db()
    assert not source.is_owner
    assert Membership.objects.get(pk=target["id"]).is_owner
    assert OrganizationChangeEvent.objects.filter(organization_id=org.id).count() == 2
    assert (
        client.post(
            base + "transfer-owner/",
            {"target_membership_id": target["id"], "version": 2, "reason": "Replay"},
            format="json",
        ).status_code
        == 403
    )


def test_direct_interface_revalidates_forged_or_stale_scope(org_setup):
    from dataclasses import replace

    from rest_framework.exceptions import NotFound, PermissionDenied

    from modules.organizations.interfaces import get_membership, resolve_scope
    from modules.organizations.models import Membership

    client, org, owner, member, outsider, _ = org_setup
    source = Membership.objects.get(organization_id=org.id, user=owner)
    scope = resolve_scope(owner.id, org.id)
    with pytest.raises(NotFound):
        get_membership(replace(scope, actor_id=outsider.id), source.id)
    Membership.objects.create(organization_id=org.id, user=member)
    with pytest.raises(PermissionDenied):
        get_membership(replace(scope, actor_id=member.id), source.id)


def test_invalid_input_is_atomic_and_unknown_fields_rejected(org_setup):
    from modules.organizations.models import Membership, Organization

    client, org, owner, member, _, operator = org_setup
    client.force_authenticate(operator)
    for patch in [
        {"timezone": "../bad"},
        {"owner_user_id": "00000000-0000-0000-0000-000000000000"},
        {"name": " "},
        {"is_owner": True},
    ]:
        data = {"name": "Bad", "timezone": "UTC", "owner_user_id": str(owner.id), **patch}
        assert client.post("/api/v1/organizations/", data, format="json").status_code == 400
    assert Organization.objects.count() == 1
    assert Membership.objects.count() == 1
    client.force_authenticate(owner)
    for query in ["?page=0", "?page_size=101", "?page=no", "?other=x", "?page=1&page=2"]:
        assert client.get("/api/v1/organizations/" + query).status_code == 400
    assert client.get("/api/v1/organizations/?page=2").status_code == 404


def test_csrf_and_anonymous_rejection(org_setup):
    _, org, owner, member, *_ = org_setup
    client = APIClient(enforce_csrf_checks=True)
    assert client.get("/api/v1/organizations/").status_code == 403
    client.force_login(owner)
    assert (
        client.post(
            f"/api/v1/organizations/{org.id}/memberships/",
            {"user_id": str(member.id)},
            format="json",
        ).status_code
        == 403
    )
    token = client.get("/api/v1/auth/session/").json()["csrf_token"]
    assert (
        client.post(
            f"/api/v1/organizations/{org.id}/memberships/",
            {"user_id": str(member.id)},
            format="json",
            HTTP_X_CSRFTOKEN=token,
        ).status_code
        == 201
    )


def test_event_failure_rolls_back_bootstrap(org_setup, monkeypatch):
    from modules.organizations import interfaces
    from modules.organizations.models import Membership, Organization

    _, _, owner, _, _, operator = org_setup

    def fail(*args, **kwargs):
        raise RuntimeError("Simulated event failure")

    monkeypatch.setattr(interfaces.OrganizationChangeEvent.objects, "create", fail)
    with pytest.raises(RuntimeError):
        interfaces.create_organization(operator.id, "Rolled back", "UTC", owner.id)
    assert Organization.objects.count() == Membership.objects.count() == 1


@pytest.mark.django_db(transaction=True)
def test_concurrent_transfers_preserve_one_owner(org_setup):
    from concurrent.futures import ThreadPoolExecutor

    from django.db import close_old_connections
    from rest_framework.exceptions import APIException

    from modules.organizations.interfaces import add_membership, transfer_owner
    from modules.organizations.models import Membership

    _, org, owner, member, outsider, _ = org_setup
    targets = [add_membership(owner.id, org.id, user.id) for user in (member, outsider)]

    def transfer(target):
        close_old_connections()
        try:
            transfer_owner(owner.id, org.id, target.id, 1, "Concurrent transfer")
            return 200
        except APIException as error:
            return error.status_code
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(transfer, targets))
    assert sorted(results) == [200, 403]
    assert (
        Membership.objects.filter(organization_id=org.id, is_owner=True, status="active").count()
        == 1
    )


def test_multiple_organizations_and_pagination(org_setup):
    from modules.organizations.interfaces import create_organization

    client, org, owner, member, outsider, operator = org_setup
    second = create_organization(operator.id, "Organization B", "UTC", owner.id)
    hidden = create_organization(operator.id, "Organization C", "UTC", outsider.id)
    page = client.get("/api/v1/organizations/?page_size=1").json()
    assert page["count"] == 2 and len(page["results"]) == 1
    following = client.get(page["next"]).json()
    assert following["results"][0]["id"] == str(second.id)
    assert client.get(f"/api/v1/organizations/{hidden.id}/").status_code == 404
    assert client.get(f"/api/v1/organizations/{org.id}/")["Cache-Control"].find("no-store") >= 0


def test_operator_permission_does_not_grant_membership(org_setup):
    from django.contrib.auth.models import Permission

    client, org, owner, member, staff, _ = org_setup
    client.force_authenticate(staff)
    data = {"name": "Provisioned", "timezone": "UTC", "owner_user_id": str(owner.id)}
    assert client.post("/api/v1/organizations/", data, format="json").status_code == 403
    staff.user_permissions.add(Permission.objects.get(codename="bootstrap_organization"))
    response = client.post("/api/v1/organizations/", data, format="json")
    assert response.status_code == 201
    assert response.json()["membership_id"] is None
    assert client.get(f"/api/v1/organizations/{response.json()['id']}/").status_code == 404


@pytest.mark.django_db(transaction=True)
def test_concurrent_last_owner_removals(org_setup):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from django.db import close_old_connections
    from rest_framework.exceptions import APIException

    from modules.organizations.interfaces import change_membership
    from modules.organizations.models import Membership

    _, org, owner, member, *_ = org_setup
    first = Membership.objects.get(organization_id=org.id, user=owner)
    second = Membership.objects.create(organization_id=org.id, user=member, is_owner=True)
    barrier = Barrier(2)

    def end_own(membership):
        close_old_connections()
        try:
            barrier.wait(timeout=5)
            change_membership(membership.user_id, org.id, membership.id, "ended", 1, "Leave")
            return 200
        except APIException as error:
            return error.status_code
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses = list(pool.map(end_own, [first, second]))
    assert sorted(statuses) == [200, 409]
    assert (
        Membership.objects.filter(organization_id=org.id, is_owner=True, status="active").count()
        == 1
    )


@pytest.mark.django_db(transaction=True)
def test_upgrade_preserves_users_without_assigning_memberships(django_user_model):
    from django.db import connection
    from django.db.migrations.executor import MigrationExecutor

    executor = MigrationExecutor(connection)
    latest = executor.loader.graph.leaf_nodes()
    executor.migrate([("organizations", None)])
    try:
        user = django_user_model.objects.create_user(username="pre-migration-user")
        executor = MigrationExecutor(connection)
        executor.migrate(latest)
        from modules.organizations.models import Membership, Organization

        assert django_user_model.objects.filter(pk=user.id).exists()
        assert Membership.objects.count() == Organization.objects.count() == 0
    finally:
        MigrationExecutor(connection).migrate(latest)
