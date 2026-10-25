"""Project ownership, current private access, and command transaction boundary."""

from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID

from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import NotFound, ValidationError

from common.api import Conflict, paginate, reason_text
from modules.clients.interfaces import get_client_summary, lock_active_client
from modules.identity.interfaces import (
    ProjectScopeDTO,
    authorize,
    get_effective_permissions,
    project_roles,
    validate_project_delegation,
)
from modules.organizations.interfaces import lock_scope, resolve_assignment_target, resolve_scope

from .models import Project, ProjectAccess, ProjectChangeEvent

PROJECT_KEYS = (
    "projects.read",
    "projects.manage",
    "projects.transition",
    "projects.reopen",
    "projects.restore",
    "projects.access.read",
    "projects.access.manage",
)


@dataclass(frozen=True)
class ProjectDTO:
    id: UUID
    code: str
    name: str
    type: str
    status: str
    client_id: UUID | None
    client_name: str
    description: str
    start_date: date | None
    target_end_date: date | None
    version: int
    created_at: datetime
    capabilities: tuple[str, ...]


@dataclass(frozen=True)
class AccessDTO:
    id: UUID
    membership_id: UUID
    member_name: str
    role_id: UUID
    role_name: str
    started_at: datetime
    ended_at: datetime | None
    version: int


def _roles(scope, project_id):
    ids = ProjectAccess.objects.filter(
        organization_id=scope.organization_id,
        project_id=project_id,
        membership_id=scope.membership_id,
        ended_at__isnull=True,
    ).values_list("role_id", flat=True)
    return tuple(r for r in project_roles(scope, ids) if r.status == "active")


def resolve_project_scope(actor_id, organization_id, project_id):
    scope = resolve_scope(actor_id, organization_id)
    if not Project.objects.filter(pk=project_id, organization_id=organization_id).exists():
        raise NotFound("Project not found.")
    roles = _roles(scope, project_id)
    effective = get_effective_permissions(scope)
    if (
        not scope.is_owner
        and "projects.read_all" not in effective.permissions
        and not any("projects.read" in r.permissions for r in roles)
    ):
        raise NotFound("Project not found.")
    return ProjectScopeDTO(
        scope.organization_id, project_id, scope.membership_id, tuple(r.id for r in roles)
    )


def _capabilities(scope, project_id):
    keys = set(get_effective_permissions(scope).permissions)
    for role in _roles(scope, project_id):
        keys.update(role.permissions)
    result = keys.intersection(PROJECT_KEYS)
    if "projects.read_all" in keys:
        result.add("projects.read")
    return tuple(sorted(result))


def _find(scope, project_id, permission="projects.read", lock=False):
    resolve_project_scope(scope.actor_id, scope.organization_id, project_id)
    if (
        permission != "projects.read"
        or "projects.read_all" not in get_effective_permissions(scope).permissions
    ):
        authorize(scope, permission, project_id)
    query = Project.objects.select_for_update() if lock else Project.objects
    return query.get(pk=project_id, organization_id=scope.organization_id)


def _dto(scope, project, clients=None, capabilities=None):
    client = (
        (
            clients.get(project.client_id)
            if clients is not None
            else get_client_summary(scope, project.client_id)
        )
        if project.client_id
        else None
    )
    return ProjectDTO(
        project.id,
        project.code,
        project.name,
        project.type,
        project.status,
        project.client_id,
        client.name if client else "",
        project.description,
        project.start_date,
        project.target_end_date,
        project.version,
        project.created_at,
        _capabilities(scope, project.id) if capabilities is None else capabilities,
    )


def _access_dto(scope, grant):
    from modules.organizations.interfaces import get_assignment_target_summary

    member = get_assignment_target_summary(scope, grant.membership_id)
    roles = project_roles(scope, [grant.role_id])
    return AccessDTO(
        grant.id,
        grant.membership_id,
        member.display_name or member.username,
        grant.role_id,
        roles[0].name if roles else "Unavailable role",
        grant.started_at,
        grant.ended_at,
        grant.version,
    )


def visible_project_ids(scope):
    current = resolve_scope(scope.actor_id, scope.organization_id)
    query = Project.objects.filter(organization_id=current.organization_id)
    if current.is_owner or "projects.read_all" in get_effective_permissions(current).permissions:
        return query.values_list("id", flat=True)
    readable = [
        r.id
        for r in project_roles(current)
        if r.status == "active" and "projects.read" in r.permissions
    ]
    return (
        query.filter(
            projectaccess__membership_id=current.membership_id,
            projectaccess__ended_at__isnull=True,
            projectaccess__role_id__in=readable,
        )
        .values_list("id", flat=True)
        .distinct()
    )


@dataclass(frozen=True)
class ProjectCapabilityDTO:
    id: UUID
    capabilities: tuple[str, ...]


def get_admin_project_capabilities(scope):
    """Current read-visible project capabilities for one Admin request; never mutation authority."""
    current = resolve_scope(scope.actor_id, scope.organization_id)
    effective = set(get_effective_permissions(current).permissions)
    roles = {r.id: set(r.permissions) for r in project_roles(current) if r.status == "active"}
    grants = ProjectAccess.objects.filter(
        organization_id=current.organization_id,
        membership_id=current.membership_id,
        ended_at__isnull=True,
    ).values_list("project_id", "role_id")
    by_project = {}
    for project_id, role_id in grants:
        by_project.setdefault(project_id, set()).update(roles.get(role_id, ()))
    result = []
    for project_id in Project.objects.filter(organization_id=current.organization_id).values_list(
        "id", flat=True
    ):
        granted = by_project.get(project_id, set())
        if (
            not current.is_owner
            and "projects.read_all" not in effective
            and "projects.read" not in granted
        ):
            continue
        keys = (effective | granted) & set(PROJECT_KEYS)
        if "projects.read_all" in effective:
            keys.add("projects.read")
        result.append(ProjectCapabilityDTO(project_id, tuple(sorted(keys))))
    return tuple(result)


def list_projects(
    scope, page=1, page_size=50, search="", status=None, type=None, client_id=None, ordering="name"
):
    current = resolve_scope(scope.actor_id, scope.organization_id)
    if ordering not in {"name", "-name", "code", "-code"} or len(search) > 100:
        raise ValidationError(
            {"detail": "Use an allowed ordering and search up to 100 characters."}
        )
    query = Project.objects.filter(id__in=visible_project_ids(current))
    for field, value, allowed in [
        ("status", status, {"draft", "active", "completed", "archived"}),
        ("type", type, {"delivery", "operations"}),
    ]:
        if value is not None:
            if value not in allowed:
                raise ValidationError({field: "Unknown value."})
            query = query.filter(**{field: value})
    if client_id:
        try:
            client_id = UUID(str(client_id))
        except ValueError:
            raise ValidationError({"client_id": "Use a valid client ID."}) from None
        query = query.filter(client_id=client_id)
    if search.strip():
        query = query.filter(Q(name__icontains=search.strip()) | Q(code__icontains=search.strip()))
    from common.api import PageDTO
    from modules.clients.interfaces import get_client_summaries

    records = paginate(query.order_by(ordering, "id"), page, page_size, lambda p: p)
    clients = {
        c.id: c
        for c in get_client_summaries(
            current, {p.client_id for p in records.results if p.client_id}
        )
    }
    return PageDTO(
        records.count, tuple(_dto(current, p, clients, ("projects.read",)) for p in records.results)
    )


def get_project(scope, project_id):
    current = resolve_scope(scope.actor_id, scope.organization_id)
    return _dto(current, _find(current, project_id))


def _fields(changes):
    for key, maximum in [("code", 32), ("name", 200), ("description", 4000)]:
        if key in changes:
            value = changes[key]
            if (
                not isinstance(value, str)
                or len(value) > maximum
                or (key != "description" and not value.strip())
            ):
                raise ValidationError({key: "Provide a valid text value."})
            changes[key] = value.strip()
    return changes


def _dates(start, end):
    if start and end and end < start:
        raise ValidationError({"target_end_date": "End date cannot precede start date."})


def _event(scope, project, action, reason, fields=(), before=0, access=None):
    ProjectChangeEvent.objects.create(
        organization_id=scope.organization_id,
        project=project,
        access=access,
        actor_id=scope.actor_id,
        action=action,
        reason=reason,
        changed_fields=list(fields),
        before_version=before,
        after_version=access.version if access else project.version,
    )


@transaction.atomic
def create_project(
    scope,
    *,
    code,
    name,
    type,
    initial_manager_membership_id,
    initial_manager_role_id,
    client_id=None,
    description="",
    start_date=None,
    target_end_date=None,
):
    _, current = lock_scope(scope.actor_id, scope.organization_id)
    authorize(current, "projects.create")
    member = resolve_assignment_target(current, initial_manager_membership_id)
    role = validate_project_delegation(current, initial_manager_role_id)
    if not {"projects.manage", "projects.access.manage"}.issubset(role.permissions):
        raise ValidationError(
            {
                "initial_manager_role_id": (
                    "Choose a manager role with read, manage and access.manage permissions."
                )
            }
        )
    if client_id:
        lock_active_client(current, client_id)
    fields = _fields(dict(code=code, name=name, description=description))
    normalized = fields["code"].casefold()
    if len(normalized) > 32 or type not in {"delivery", "operations"}:
        raise ValidationError({"detail": "Invalid code or project type."})
    _dates(start_date, target_end_date)
    try:
        with transaction.atomic():
            project = Project.objects.create(
                organization_id=current.organization_id,
                normalized_code=normalized,
                type=type,
                client_id=client_id,
                start_date=start_date,
                target_end_date=target_end_date,
                **fields,
            )
    except IntegrityError:
        raise Conflict("A project with this code already exists in this organization.") from None
    grant = ProjectAccess.objects.create(
        organization_id=current.organization_id,
        project=project,
        membership_id=member,
        role_id=role.id,
    )
    _event(current, project, "created", "Project created", fields)
    _event(current, project, "access_granted", "Initial manager selected", access=grant)
    capabilities = (
        _capabilities(current, project.id)
        if current.is_owner
        or "projects.read_all" in get_effective_permissions(current).permissions
        or member == current.membership_id
        else ()
    )
    client_name = get_client_summary(current, client_id).name if client_id else ""
    return ProjectDTO(
        project.id,
        project.code,
        project.name,
        project.type,
        project.status,
        project.client_id,
        client_name,
        project.description,
        project.start_date,
        project.target_end_date,
        project.version,
        project.created_at,
        capabilities,
    )


@transaction.atomic
def update_project(scope, project_id, *, version, reason, **changes):
    _, current = lock_scope(scope.actor_id, scope.organization_id)
    project = _find(current, project_id, "projects.manage", True)
    if project.version != version or project.status == "archived":
        raise Conflict("Project changed or is archived. Refresh before editing.")
    reason = reason_text(reason)
    if not changes or set(changes) - {"name", "description", "start_date", "target_end_date"}:
        raise ValidationError({"detail": "Only name, description and planned dates can change."})
    changes = _fields(changes)
    _dates(
        changes.get("start_date", project.start_date),
        changes.get("target_end_date", project.target_end_date),
    )
    for key, value in changes.items():
        setattr(project, key, value)
    project.version += 1
    project.save(update_fields=[*changes, "version"])
    _event(current, project, "updated", reason, changes, version)
    return _dto(current, project)


@transaction.atomic
def transition_project(scope, project_id, *, target_status, version, reason):
    _, current = lock_scope(scope.actor_id, scope.organization_id)
    project = _find(current, project_id, lock=True)
    key = (
        "projects.restore"
        if project.status == "archived"
        else "projects.reopen"
        if project.status == "completed" and target_status == "active"
        else "projects.transition"
    )
    authorize(current, key, project.id)
    allowed = {
        "draft": {"active", "archived"},
        "active": {"completed", "archived"},
        "completed": {"active", "archived"},
        "archived": {"draft"},
    }
    if version != project.version or target_status not in allowed[project.status]:
        raise Conflict("Project changed or this transition is not allowed.")
    reason = reason_text(reason)
    project.status = target_status
    project.version += 1
    project.save(update_fields=["status", "version"])
    _event(current, project, "transitioned", reason, ["status"], version)
    return _dto(current, project)


def list_access(scope, project_id, page=1, page_size=50):
    current = resolve_scope(scope.actor_id, scope.organization_id)
    _find(current, project_id, "projects.access.read")
    records = paginate(
        ProjectAccess.objects.filter(project_id=project_id).order_by("-started_at", "id"),
        page,
        page_size,
        lambda g: g,
    )
    from common.api import PageDTO

    return PageDTO(records.count, _access_dtos(current, records.results))


def _access_dtos(scope, grants):
    from modules.organizations.interfaces import get_assignment_target_summaries

    members = {
        m.id: m for m in get_assignment_target_summaries(scope, {g.membership_id for g in grants})
    }
    roles = {r.id: r for r in project_roles(scope, {g.role_id for g in grants})}
    result = []
    for grant in grants:
        member = members.get(grant.membership_id)
        if member is None:
            raise NotFound("Membership not found.")
        role = roles.get(grant.role_id)
        result.append(
            AccessDTO(
                grant.id,
                grant.membership_id,
                member.display_name or member.username,
                grant.role_id,
                role.name if role else "Unavailable role",
                grant.started_at,
                grant.ended_at,
                grant.version,
            )
        )
    return tuple(result)


@transaction.atomic
def grant_access(scope, project_id, *, membership_id, role_id, reason):
    _, current = lock_scope(scope.actor_id, scope.organization_id)
    project = _find(current, project_id, "projects.access.manage", True)
    if project.status == "archived":
        raise Conflict("Restore this project before granting access.")
    member = resolve_assignment_target(current, membership_id)
    role = validate_project_delegation(current, role_id, project.id)
    reason = reason_text(reason)
    if ProjectAccess.objects.filter(
        project=project, membership_id=member, role_id=role.id, ended_at__isnull=True
    ).exists():
        raise Conflict("This member already has this live project role.")
    grant = ProjectAccess.objects.create(
        organization_id=current.organization_id,
        project=project,
        membership_id=member,
        role_id=role.id,
    )
    _event(current, project, "access_granted", reason, access=grant)
    return _access_dto(current, grant)


@transaction.atomic
def end_access(scope, project_id, grant_id, *, version, reason):
    _, current = lock_scope(scope.actor_id, scope.organization_id)
    project = _find(current, project_id, "projects.access.manage", True)
    grant = ProjectAccess.objects.filter(pk=grant_id, project=project).first()
    if grant is None:
        raise NotFound("Project access not found.")
    if grant.version != version or grant.ended_at is not None:
        raise Conflict()
    reason = reason_text(reason)
    grant.ended_at = timezone.now()
    grant.version += 1
    grant.save(update_fields=["ended_at", "version"])
    _event(current, project, "access_ended", reason, before=version, access=grant)
    return _access_dto(current, grant)


def assignment_options(scope, kind, page=1, page_size=50, search="", project_id=None):
    from modules.clients.interfaces import list_project_client_choices
    from modules.organizations.interfaces import list_assignment_targets

    current = resolve_scope(scope.actor_id, scope.organization_id)
    if kind == "filter_clients" and project_id is None:
        from common.api import PageDTO
        from modules.clients.interfaces import get_client_summaries

        ids = (
            Project.objects.filter(id__in=visible_project_ids(current), client_id__isnull=False)
            .order_by("client_id")
            .values_list("client_id", flat=True)
            .distinct()
        )
        result = paginate(ids, page, page_size, lambda value: value)
        clients = get_client_summaries(current, result.results)
        if search:
            raise ValidationError({"search": "Use the client list pages to choose this filter."})
        return PageDTO(result.count, clients)
    if project_id:
        _find(current, project_id, "projects.access.manage")
    else:
        authorize(current, "projects.create")
    if kind == "members":
        return list_assignment_targets(current, page, page_size, search)
    if kind == "clients" and not project_id:
        return list_project_client_choices(current, page, page_size, search)
    if kind != "roles":
        raise ValidationError({"kind": "Choose members, roles or clients."})
    if page < 1 or not 1 <= page_size <= 100 or len(search) > 100:
        raise ValidationError({"detail": "Invalid pagination or search."})
    allowed = []
    held = set(get_effective_permissions(current).permissions)
    if project_id:
        for assigned_role in _roles(current, project_id):
            held.update(assigned_role.permissions)
    for role in project_roles(current):
        if search.casefold() not in role.name.casefold():
            continue
        if (
            role.status != "active"
            or "projects.read" not in role.permissions
            or not set(role.permissions).issubset(held)
        ):
            continue
        if not project_id and not {"projects.manage", "projects.access.manage"}.issubset(
            role.permissions
        ):
            continue
        allowed.append(role)
    from common.api import PageDTO

    return PageDTO(len(allowed), tuple(allowed[(page - 1) * page_size : page * page_size]))


@dataclass(frozen=True)
class ProjectWorkerDTO:
    id: UUID
    resource_id: UUID
    resource_name: str
    started_at: datetime
    ended_at: datetime | None
    version: int


def _worker(item):
    return ProjectWorkerDTO(
        item.id, item.resource_id, item.resource_name, item.started_at, item.ended_at, item.version
    )


def list_workers(scope, project_id, page=1, page_size=50):
    from .models import ProjectWorker

    current = resolve_scope(scope.actor_id, scope.organization_id)
    project = _find(current, project_id)
    return paginate(
        ProjectWorker.objects.filter(project=project).order_by("-started_at", "id"),
        page,
        page_size,
        _worker,
    )


def worker_options(scope, project_id, kind, page=1, page_size=50, search=""):
    from modules.resources.interfaces import assignment_choices

    current = resolve_scope(scope.actor_id, scope.organization_id)
    _find(current, project_id, "projects.manage")
    return assignment_choices(current, kind, page, page_size, search)


@transaction.atomic
def add_worker(scope, project_id, *, resource_id=None, membership_id=None, reason):
    from modules.resources.interfaces import resolve_worker_for_assignment

    from .models import ProjectWorker

    _, current = lock_scope(scope.actor_id, scope.organization_id)
    project = _find(current, project_id, "projects.manage", True)
    if project.status == "archived":
        raise Conflict("Restore this project before adding workers.")
    reason = reason_text(reason)
    resource = resolve_worker_for_assignment(
        current, resource_id=resource_id, membership_id=membership_id
    )
    if ProjectWorker.objects.filter(
        project=project, resource_id=resource.id, ended_at__isnull=True
    ).exists():
        raise Conflict("This worker is already on this project.")
    item = ProjectWorker.objects.create(
        organization_id=current.organization_id,
        project=project,
        resource_id=resource.id,
        resource_name=resource.display_name,
        added_by=current.actor_id,
        reason=reason,
    )
    return _worker(item)


@transaction.atomic
def end_worker(scope, project_id, worker_id, *, version, reason):
    from .models import ProjectWorker

    _, current = lock_scope(scope.actor_id, scope.organization_id)
    project = _find(current, project_id, "projects.manage", True)
    item = ProjectWorker.objects.filter(project=project, pk=worker_id).first()
    if item is None:
        raise NotFound("Worker assignment not found.")
    if item.version != version or item.ended_at is not None:
        raise Conflict()
    item.end_reason = reason_text(reason)
    item.ended_at = timezone.now()
    item.ended_by = current.actor_id
    item.version += 1
    item.save(update_fields=["end_reason", "ended_at", "ended_by", "version"])
    return _worker(item)
