"""Independent PostgreSQL connections exercise the shared organization lock."""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier

import pytest
from django.db import close_old_connections, connections
from django.utils import timezone

from common.api import Conflict
from modules.clients.interfaces import create_client, list_clients
from modules.organizations.interfaces import create_organization, resolve_scope
from modules.resources.interfaces import (
    assign_team_member,
    create_resource,
    create_team,
    get_team_members,
)

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def scope(django_user_model):
    owner = django_user_model.objects.create_superuser(username="race-owner")
    org = create_organization(owner.pk, "Concurrency", "UTC", owner.pk)
    return resolve_scope(owner.pk, org.id)


def race(command):
    ready = Barrier(2)

    def execute():
        close_old_connections()
        try:
            ready.wait(timeout=10)
            command()
            return "saved"
        except Conflict:
            return "conflict"
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as workers:
        futures = [workers.submit(execute) for _ in range(2)]
        return sorted(future.result(timeout=20) for future in futures)


def test_concurrent_duplicate_client_creates_one_record(scope):
    assert race(lambda: create_client(scope, "SAME", "Client")) == ["conflict", "saved"]
    assert list_clients(scope).count == 1


def test_concurrent_overlapping_intervals_create_one_membership(scope):
    person = create_resource(scope, "P1", "Person")
    team = create_team(scope, "T1", "Team")
    today = timezone.now().date()
    assert race(
        lambda: assign_team_member(scope, team.id, person.id, today, today + timedelta(days=2))
    ) == ["conflict", "saved"]
    assert get_team_members(scope, team.id).count == 1


def test_concurrent_project_edits_reject_stale_writer(scope):
    from modules.identity.interfaces import create_role
    from modules.projects.interfaces import create_project, get_project, update_project

    role = create_role(
        scope.actor_id,
        scope.organization_id,
        "Manager",
        ["projects.read", "projects.manage", "projects.access.manage"],
        "project",
    )
    project = create_project(
        scope,
        code="RACE",
        name="Project",
        type="delivery",
        initial_manager_membership_id=scope.membership_id,
        initial_manager_role_id=role.id,
    )
    assert race(
        lambda: update_project(scope, project.id, version=1, reason="Concurrent edit", name="Saved")
    ) == ["conflict", "saved"]
    assert get_project(scope, project.id).version == 2
