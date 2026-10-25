"""Owned commands and frozen public summaries for stable people and team history."""

from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID
from zoneinfo import ZoneInfo

from django.db import IntegrityError, transaction
from django.db.models import Prefetch, Q
from django.utils import timezone
from rest_framework.exceptions import NotFound, ValidationError

from common.api import Conflict, paginate, reason_text
from modules.identity.interfaces import authorize
from modules.organizations.interfaces import lock_scope, resolve_assignment_target, resolve_scope

from .models import Resource, ResourceChangeEvent, ResourceIdentityLink, Team, TeamMembership


@dataclass(frozen=True)
class ResourceSummaryDTO:
    id: UUID
    code: str
    display_name: str
    status: str
    version: int
    linked_membership_id: UUID | None


@dataclass(frozen=True)
class TeamDTO:
    id: UUID
    code: str
    name: str
    status: str
    version: int


@dataclass(frozen=True)
class LinkDTO:
    id: UUID
    resource_id: UUID
    membership_id: UUID
    started_at: datetime
    ended_at: datetime | None
    reason: str
    resource_version: int


@dataclass(frozen=True)
class TeamMembershipDTO:
    id: UUID
    team_id: UUID
    resource_id: UUID
    resource_name: str
    resource_status: str
    start_date: date
    end_date: date | None
    version: int


def _resource(item):
    links = getattr(item, "current_identity_links", None)
    link = links[0] if links else None
    if links is None:
        link = item.resourceidentitylink_set.filter(ended_at__isnull=True).first()
    return ResourceSummaryDTO(
        item.id,
        item.code,
        item.display_name,
        item.status,
        item.version,
        link.membership_id if link else None,
    )


def _team(item):
    return TeamDTO(item.id, item.code, item.name, item.status, item.version)


def _link(item):
    return LinkDTO(
        item.id,
        item.resource_id,
        item.membership_id,
        item.started_at,
        item.ended_at,
        item.reason,
        item.resource.version,
    )


def _assignment(item):
    return TeamMembershipDTO(
        item.id,
        item.team_id,
        item.resource_id,
        item.resource.display_name,
        item.resource.status,
        item.start_date,
        item.end_date,
        item.version,
    )


def _find(model, org, pk):
    item = model.objects.filter(organization_id=org, pk=pk).first()
    if item is None:
        raise NotFound("Record not found.")
    return item


def _scope(scope, permission):
    current = resolve_scope(scope.actor_id, scope.organization_id)
    authorize(current, permission)
    return current


def _event(scope, entity, action, reason, **details):
    ResourceChangeEvent.objects.create(
        organization_id=scope.organization_id,
        actor_id=scope.actor_id,
        entity_id=entity.id,
        entity_type=entity._meta.model_name,
        action=action,
        reason=reason,
        details=details,
    )


def _text(value, key, maximum):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ValidationError({key: f"Provide 1–{maximum} characters."})
    return value.strip()


def _version(item, version):
    if item.version != version:
        raise Conflict()


def _date(value):
    if not isinstance(value, date) or isinstance(value, datetime):
        raise ValidationError({"date": "Use a valid business date."})
    return value


def get_resource_summary(scope, resource_id):
    current = _scope(scope, "resources.read")
    return _resource(_find(Resource, current.organization_id, resource_id))


def get_team(scope, team_id):
    current = _scope(scope, "teams.read")
    return _team(_find(Team, current.organization_id, team_id))


def _list(scope, model, page, page_size, search, status):
    is_resource = model is Resource
    current = _scope(scope, "resources.read" if is_resource else "teams.read")
    if not isinstance(search, str) or len(search) > 100:
        raise ValidationError({"search": "Maximum 100 characters."})
    query = model.objects.filter(organization_id=current.organization_id)
    if status:
        if status not in {"active", "retired" if is_resource else "archived"}:
            raise ValidationError({"status": "Unknown status."})
        query = query.filter(status=status)
    name = "display_name" if is_resource else "name"
    if search.strip():
        query = query.filter(
            Q(**{name + "__icontains": search.strip()}) | Q(code__icontains=search.strip())
        )
    if is_resource:
        query = query.prefetch_related(
            Prefetch(
                "resourceidentitylink_set",
                queryset=ResourceIdentityLink.objects.filter(ended_at__isnull=True),
                to_attr="current_identity_links",
            )
        )
    return paginate(
        query.order_by(name, "id"), page, page_size, _resource if is_resource else _team
    )


def list_resources(scope, page=1, page_size=50, search="", status=None):
    return _list(scope, Resource, page, page_size, search, status)


def list_teams(scope, page=1, page_size=50, search="", status=None):
    return _list(scope, Team, page, page_size, search, status)


@transaction.atomic
def _create(scope, model, code, name):
    _, current = lock_scope(scope.actor_id, scope.organization_id)
    is_resource = model is Resource
    authorize(current, "resources.manage" if is_resource else "teams.manage")
    code = _text(code, "code", 32)
    normalized = code.casefold()
    if len(normalized) > 32:
        raise ValidationError({"code": "Normalized code exceeds 32 characters."})
    field = "display_name" if is_resource else "name"
    name = _text(name, field, 200)
    try:
        with transaction.atomic():
            item = model.objects.create(
                organization_id=current.organization_id,
                code=code,
                normalized_code=normalized,
                **{field: name},
            )
    except IntegrityError:
        raise Conflict("This code already exists in this organization.") from None
    _event(current, item, "created", "Record created")
    return _resource(item) if is_resource else _team(item)


def create_resource(scope, code="", display_name=""):
    from uuid import uuid4

    return _create(scope, Resource, code or uuid4().hex, display_name)


def create_team(scope, code, name):
    return _create(scope, Team, code, name)


@transaction.atomic
def _update(scope, model, pk, version, reason, changes):
    _, current = lock_scope(scope.actor_id, scope.organization_id)
    is_resource = model is Resource
    authorize(current, "resources.manage" if is_resource else "teams.manage")
    item = _find(model, current.organization_id, pk)
    _version(item, version)
    reason = reason_text(reason)
    field = "display_name" if is_resource else "name"
    if not changes or set(changes) - {field, "status"}:
        raise ValidationError({"detail": "Provide editable fields; code is immutable."})
    if field in changes:
        changes[field] = _text(changes[field], field, 200)
    if "status" in changes and changes["status"] not in {
        "active",
        "retired" if is_resource else "archived",
    }:
        raise ValidationError({"status": "Unknown status."})
    changed = [key for key, value in changes.items() if getattr(item, key) != value]
    if changed:
        for key in changed:
            setattr(item, key, changes[key])
        item.version += 1
        item.save(update_fields=[*changed, "version"])
        _event(current, item, "updated", reason, fields=changed, version=item.version)
    return _resource(item) if is_resource else _team(item)


def update_resource(scope, resource_id, *, version, reason, **changes):
    return _update(scope, Resource, resource_id, version, reason, changes)


def update_team(scope, team_id, *, version, reason, **changes):
    return _update(scope, Team, team_id, version, reason, changes)


def list_identity_links(scope, resource_id, page=1, page_size=50):
    current = _scope(scope, "resources.read")
    resource = _find(Resource, current.organization_id, resource_id)
    return paginate(
        ResourceIdentityLink.objects.filter(resource=resource)
        .select_related("resource")
        .order_by("-started_at", "id"),
        page,
        page_size,
        _link,
    )


@transaction.atomic
def link_identity(scope, resource_id, membership_id, version, reason):
    _, current = lock_scope(scope.actor_id, scope.organization_id)
    authorize(current, "resources.link_identity")
    resource = _find(Resource, current.organization_id, resource_id)
    _version(resource, version)
    reason = reason_text(reason)
    if resource.status != "active":
        raise Conflict("Reactivate the person before linking a login.")
    membership_id = resolve_assignment_target(current, membership_id)
    try:
        with transaction.atomic():
            link = ResourceIdentityLink.objects.create(
                organization_id=current.organization_id,
                resource=resource,
                membership_id=membership_id,
                reason=reason,
            )
    except IntegrityError:
        raise Conflict("This person or membership already has a live login link.") from None
    resource.version += 1
    resource.save(update_fields=["version"])
    _event(
        current,
        resource,
        "identity_linked",
        reason,
        link_id=str(link.id),
        membership_id=str(membership_id),
        version=resource.version,
    )
    return _link(link)


@transaction.atomic
def end_identity_link(scope, resource_id, link_id, version, reason):
    _, current = lock_scope(scope.actor_id, scope.organization_id)
    authorize(current, "resources.link_identity")
    resource = _find(Resource, current.organization_id, resource_id)
    _version(resource, version)
    link = ResourceIdentityLink.objects.filter(resource=resource, pk=link_id).first()
    if link is None:
        raise NotFound()
    if link.ended_at is not None:
        raise Conflict("This link has already ended.")
    reason = reason_text(reason)
    link.ended_at = timezone.now()
    link.save(update_fields=["ended_at"])
    resource.version += 1
    resource.save(update_fields=["version"])
    _event(
        current,
        resource,
        "identity_unlinked",
        reason,
        link_id=str(link.id),
        membership_id=str(link.membership_id),
        version=resource.version,
    )
    return _link(link)


def get_team_members(scope, team_id, as_of=None, page=1, page_size=50):
    current = _scope(scope, "teams.read")
    team = _find(Team, current.organization_id, team_id)
    query = TeamMembership.objects.filter(team=team).select_related("resource")
    if as_of is not None:
        _date(as_of)
        query = query.filter(start_date__lte=as_of).filter(
            Q(end_date__isnull=True) | Q(end_date__gt=as_of)
        )
    return paginate(query.order_by("-start_date", "id"), page, page_size, _assignment)


@transaction.atomic
def assign_team_member(
    scope, team_id, resource_id=None, start_date=None, end_date=None, membership_id=None
):
    org, current = lock_scope(scope.actor_id, scope.organization_id)
    authorize(current, "teams.manage")
    team = _find(Team, current.organization_id, team_id)
    worker = resolve_worker_for_assignment(
        current, resource_id=resource_id, membership_id=membership_id
    )
    resource = _find(Resource, current.organization_id, worker.id)
    today = timezone.localdate(timezone=ZoneInfo(org.timezone))
    if _date(start_date) < today or (end_date is not None and _date(end_date) <= start_date):
        raise ValidationError(
            {"start_date": "Start must be today or later; end must be after start."}
        )
    if team.status != "active" or resource.status != "active":
        raise Conflict("Choose an active team and person.")
    overlaps = TeamMembership.objects.filter(team=team, resource=resource).filter(
        Q(end_date__isnull=True) | Q(end_date__gt=start_date)
    )
    if end_date is not None:
        overlaps = overlaps.filter(start_date__lt=end_date)
    if overlaps.exists():
        raise Conflict("This person already has an overlapping interval in this team.")
    item = TeamMembership.objects.create(
        organization_id=current.organization_id,
        team=team,
        resource=resource,
        start_date=start_date,
        end_date=end_date,
    )
    _event(
        current,
        item,
        "assigned",
        "Team assignment created",
        team_id=str(team.id),
        resource_id=str(resource.id),
        start_date=str(start_date),
        end_date=str(end_date) if end_date else None,
    )
    return _assignment(item)


@transaction.atomic
def end_team_membership(scope, team_id, membership_id, end_date, version, reason):
    org, current = lock_scope(scope.actor_id, scope.organization_id)
    authorize(current, "teams.manage")
    team = _find(Team, current.organization_id, team_id)
    item = (
        TeamMembership.objects.select_related("resource")
        .filter(team=team, pk=membership_id)
        .first()
    )
    if item is None:
        raise NotFound()
    _version(item, version)
    reason = reason_text(reason)
    today = timezone.localdate(timezone=ZoneInfo(org.timezone))
    if item.end_date is not None and item.end_date <= today:
        raise Conflict("Ended history cannot be rewritten.")
    if _date(end_date) < today or end_date <= item.start_date:
        raise ValidationError({"end_date": "End must be today or later and strictly after start."})
    overlaps = (
        TeamMembership.objects.filter(team=team, resource=item.resource)
        .exclude(pk=item.pk)
        .filter(start_date__lt=end_date)
        .filter(Q(end_date__isnull=True) | Q(end_date__gt=item.start_date))
    )
    if overlaps.exists():
        raise Conflict("This end date overlaps another team interval.")
    before = item.end_date
    if before != end_date:
        item.end_date = end_date
        item.version += 1
        item.save(update_fields=["end_date", "version"])
        _event(
            current,
            item,
            "ended",
            reason,
            previous_end=str(before) if before else None,
            end_date=str(end_date),
            version=item.version,
        )
    return _assignment(item)


@dataclass(frozen=True)
class WorkerChoiceDTO:
    id: UUID
    label: str


def assignment_choices(scope, kind, page=1, page_size=50, search=""):
    """Trusted minimal choices; caller authorizes team/project/resource use case."""
    from common.api import PageDTO
    from modules.organizations.interfaces import list_assignment_targets

    current = resolve_scope(scope.actor_id, scope.organization_id)
    if kind == "members":
        result = list_assignment_targets(current, page, page_size, search)
        return PageDTO(
            result.count,
            tuple(
                WorkerChoiceDTO(m.id, f"{m.display_name or m.username} (@{m.username})")
                for m in result.results
            ),
        )
    if kind != "resources" or not isinstance(search, str) or len(search) > 100:
        raise ValidationError({"kind": "Choose members or resources; search up to 100 characters."})
    query = Resource.objects.filter(organization_id=current.organization_id, status="active")
    if search.strip():
        query = query.filter(
            Q(display_name__icontains=search.strip()) | Q(code__icontains=search.strip())
        )
    return paginate(
        query.order_by("display_name", "id"),
        page,
        page_size,
        lambda r: WorkerChoiceDTO(r.id, f"{r.display_name} ({r.code})"),
    )


def resource_choices(scope, kind, page=1, page_size=50, search=""):
    current = _scope(scope, "resources.read")
    if kind == "members":
        authorize(current, "memberships.read")
    return assignment_choices(current, kind, page, page_size, search)


def resolve_worker_for_assignment(scope, *, resource_id=None, membership_id=None):
    """Owning command must authorize and hold the organization lock in a transaction."""
    from uuid import uuid4

    from django.db import connection

    from modules.organizations.interfaces import get_assignment_target_summary

    if not connection.in_atomic_block:
        raise RuntimeError("Worker assignment requires an atomic owning command.")
    current = resolve_scope(scope.actor_id, scope.organization_id)
    if (resource_id is None) == (membership_id is None):
        raise ValidationError({"detail": "Choose exactly one existing member or resource."})
    if resource_id is not None:
        item = _find(Resource, current.organization_id, resource_id)
    else:
        membership_id = resolve_assignment_target(current, membership_id)
        link = (
            ResourceIdentityLink.objects.filter(
                organization_id=current.organization_id,
                membership_id=membership_id,
                ended_at__isnull=True,
            )
            .select_related("resource")
            .first()
        )
        if link:
            item = link.resource
        else:
            if ResourceIdentityLink.objects.filter(
                organization_id=current.organization_id, membership_id=membership_id
            ).exists():
                raise Conflict(
                    "This member has an ended resource link. "
                    "Relink the existing person before assigning to preserve history."
                )
            member = get_assignment_target_summary(current, membership_id)
            code = uuid4().hex
            item = Resource.objects.create(
                organization_id=current.organization_id,
                code=code,
                normalized_code=code,
                display_name=(member.display_name or member.username)[:200],
            )
            _event(current, item, "created", "Resource derived from existing member")
            link = ResourceIdentityLink.objects.create(
                organization_id=current.organization_id,
                resource=item,
                membership_id=membership_id,
                reason="Existing member selected for work",
            )
            _event(
                current,
                item,
                "identity_linked",
                link.reason,
                link_id=str(link.id),
                membership_id=str(membership_id),
            )
    if item.status != "active":
        raise Conflict("Reactivate the existing person before assigning work.")
    return _resource(item)


@transaction.atomic
def add_resource_from_member(scope, membership_id):
    _, current = lock_scope(scope.actor_id, scope.organization_id)
    for key in ("resources.manage", "resources.link_identity", "memberships.read"):
        authorize(current, key)
    return resolve_worker_for_assignment(current, membership_id=membership_id)
