from dataclasses import asdict, dataclass
from datetime import datetime
from uuid import UUID

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.utils.module_loading import import_string
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from common.api import Conflict, paginate, reason_text
from modules.organizations.interfaces import lock_scope, resolve_assignment_target, resolve_scope

from .catalog import ALL_KEYS, PROJECT_KEYS
from .models import GrantChangeEvent, OrganizationRole, RoleAssignment, RolePermission


@dataclass(frozen=True)
class PermissionSetDTO:
    organization_id: UUID
    membership_id: UUID
    is_owner: bool
    permissions: tuple[str, ...]


@dataclass(frozen=True)
class RoleDTO:
    id: UUID
    name: str
    scope_kind: str
    status: str
    version: int
    permissions: tuple[str, ...]


@dataclass(frozen=True)
class AssignmentDTO:
    id: UUID
    membership_id: UUID
    role_id: UUID
    role_name: str
    started_at: datetime
    ended_at: datetime | None
    version: int


def role_dto(role):
    return RoleDTO(
        role.id,
        role.name,
        role.scope_kind,
        role.status,
        role.version,
        tuple(sorted(p.key for p in role.permission_records.all())),
    )


def assignment_dto(assignment):
    return AssignmentDTO(
        assignment.id,
        assignment.membership_id,
        assignment.role_id,
        assignment.role.name,
        assignment.started_at,
        assignment.ended_at,
        assignment.version,
    )


def get_effective_permissions(scope):
    current = resolve_scope(scope.actor_id, scope.organization_id)
    if current.is_owner:
        keys = ALL_KEYS
    else:
        keys = (
            set(
                RolePermission.objects.filter(
                    role__organization_id=current.organization_id,
                    role__status="active",
                    role__scope_kind="organization",
                    role__roleassignment__organization_id=current.organization_id,
                    role__roleassignment__membership_id=current.membership_id,
                    role__roleassignment__ended_at__isnull=True,
                ).values_list("key", flat=True)
            )
            & ALL_KEYS
        )
    return PermissionSetDTO(
        current.organization_id, current.membership_id, current.is_owner, tuple(sorted(keys))
    )


@dataclass(frozen=True)
class ProjectScopeDTO:
    """Returned only by the trusted projects resolver registered at composition root."""

    organization_id: UUID
    project_id: UUID
    membership_id: UUID
    role_ids: tuple[UUID, ...]


def authorize(scope, permission_key, resource_context=None):
    effective = get_effective_permissions(scope)
    if permission_key not in ALL_KEYS:
        raise PermissionDenied("Unknown permission.")
    if permission_key in PROJECT_KEYS:
        resolver = getattr(settings, "IDENTITY_PROJECT_SCOPE_RESOLVER", None)
        if not resolver or not isinstance(resource_context, UUID):
            raise PermissionDenied("Project access requires a verified project scope.")
        resolved = import_string(resolver)(
            scope.actor_id, effective.organization_id, resource_context
        )
        if not isinstance(resolved, ProjectScopeDTO) or (
            resolved.organization_id != effective.organization_id
            or resolved.project_id != resource_context
            or resolved.membership_id != effective.membership_id
        ):
            raise PermissionDenied("Project scope could not be verified.")
        if permission_key in effective.permissions:
            return
        if RolePermission.objects.filter(
            role_id__in=resolved.role_ids,
            role__organization_id=effective.organization_id,
            role__scope_kind="project",
            role__status="active",
            key=permission_key,
        ).exists():
            return
        raise PermissionDenied("You do not have permission for this project action.")
    if resource_context is not None or permission_key not in effective.permissions:
        raise PermissionDenied("You do not have permission for this action.")


def has_permission(scope, permission):
    try:
        authorize(scope, permission)
    except PermissionDenied:
        return False
    return True


def _delegation(scope, keys):
    if not set(keys).issubset(get_effective_permissions(scope).permissions):
        raise PermissionDenied("You can delegate only permissions you currently hold.")


def _keys(keys, scope_kind):
    if not isinstance(keys, (list, tuple)) or any(not isinstance(key, str) for key in keys):
        raise ValidationError({"permissions": "Use a list of permission keys."})
    allowed = ALL_KEYS if scope_kind == "organization" else PROJECT_KEYS
    if set(keys) - allowed or len(keys) != len(set(keys)):
        raise ValidationError(
            {"permissions": "Unknown, duplicate or incompatible permission keys."}
        )
    return sorted(keys)


def _name(name):
    if not isinstance(name, str) or not name.strip() or len(name) > 200:
        raise ValidationError({"name": "Provide a name of 1–200 characters."})
    return name.strip()


def _role(scope, role_id):
    role = OrganizationRole.objects.filter(
        pk=role_id, organization_id=scope.organization_id
    ).first()
    if role is None:
        raise NotFound("Role not found.")
    return role


def _event(scope, role, action, reason, before=None, assignment=None):
    result = role_dto(role)
    snapshot = asdict(result)
    snapshot.pop("id")
    GrantChangeEvent.objects.create(
        organization_id=scope.organization_id,
        actor_id=scope.actor_id,
        role=role,
        assignment=assignment,
        action=action,
        reason=reason,
        before=before or {},
        after=snapshot,
    )

    return result


def list_roles(actor_id, organization_id, page=1, page_size=50):
    scope = resolve_scope(actor_id, organization_id)
    authorize(scope, "roles.read")
    query = (
        OrganizationRole.objects.filter(organization_id=organization_id)
        .prefetch_related("permission_records")
        .order_by("name", "id")
    )
    return paginate(query, page, page_size, role_dto)


def get_role_permissions(scope, role_id):
    current = resolve_scope(scope.actor_id, scope.organization_id)
    authorize(current, "roles.read")
    role = _role(current, role_id)
    return role_dto(role).permissions


@transaction.atomic
def create_role(actor_id, organization_id, name, permissions, scope_kind="organization"):
    _, scope = lock_scope(actor_id, organization_id)
    authorize(scope, "roles.manage")
    if scope_kind not in {"organization", "project"}:
        raise ValidationError({"scope_kind": "Unknown scope."})
    name, keys = _name(name), _keys(permissions, scope_kind)
    _delegation(scope, keys)
    if OrganizationRole.objects.filter(organization_id=organization_id, name__iexact=name).exists():
        raise Conflict("A role with this name already exists.")
    role = OrganizationRole.objects.create(
        organization_id=organization_id, name=name, scope_kind=scope_kind
    )
    RolePermission.objects.bulk_create([RolePermission(role=role, key=key) for key in keys])
    return _event(scope, role, "role_created", "Role created")


@transaction.atomic
def update_role(actor_id, organization_id, role_id, version, reason, **changes):
    _, scope = lock_scope(actor_id, organization_id)
    authorize(scope, "roles.manage")
    reason = reason_text(reason)
    if set(changes) - {"name", "permissions", "status"}:
        raise ValidationError({"detail": "Unknown or immutable field."})
    role = _role(scope, role_id)
    if version != role.version:
        raise Conflict()
    before = asdict(role_dto(role))
    before.pop("id")
    old_keys = before["permissions"]
    keys = _keys(changes.get("permissions", old_keys), role.scope_kind)
    _delegation(scope, set(keys) | set(old_keys))
    name = _name(changes.get("name", role.name))
    status = changes.get("status", role.status)
    if status not in {"active", "archived"}:
        raise ValidationError({"status": "Unknown status."})
    if (
        OrganizationRole.objects.filter(organization_id=organization_id, name__iexact=name)
        .exclude(pk=role.id)
        .exists()
    ):
        raise Conflict("A role with this name already exists.")
    role.name, role.status = name, status
    role.version += 1
    role.save(update_fields=["name", "status", "version"])
    RolePermission.objects.filter(role=role).delete()
    RolePermission.objects.bulk_create([RolePermission(role=role, key=key) for key in keys])
    return _event(scope, role, "role_updated", reason, before)


def list_assignments(actor_id, organization_id, page=1, page_size=50):
    scope = resolve_scope(actor_id, organization_id)
    authorize(scope, "roles.read")
    query = (
        RoleAssignment.objects.filter(organization_id=organization_id)
        .select_related("role")
        .order_by("-started_at", "id")
    )
    return paginate(query, page, page_size, assignment_dto)


@transaction.atomic
def assign_role(actor_id, organization_id, membership_id, role_id, reason):
    _, scope = lock_scope(actor_id, organization_id)
    authorize(scope, "roles.assign")
    reason = reason_text(reason)
    target = resolve_assignment_target(scope, membership_id)
    role = _role(scope, role_id)
    _delegation(scope, role_dto(role).permissions)
    if role.status != "active" or role.scope_kind != "organization":
        raise Conflict("Choose an active organization role. Project assignments belong to 0008.")
    if RoleAssignment.objects.filter(
        membership_id=target, role=role, ended_at__isnull=True
    ).exists():
        raise Conflict("This live assignment already exists.")
    assignment = RoleAssignment.objects.create(
        organization_id=organization_id, membership_id=target, role=role
    )
    _event(scope, role, "role_assigned", reason, assignment=assignment)
    return assignment_dto(assignment)


@transaction.atomic
def revoke_assignment(actor_id, organization_id, assignment_id, version, reason):
    _, scope = lock_scope(actor_id, organization_id)
    authorize(scope, "roles.assign")
    reason = reason_text(reason)
    assignment = (
        RoleAssignment.objects.filter(pk=assignment_id, organization_id=organization_id)
        .select_related("role")
        .first()
    )
    if assignment is None:
        raise NotFound("Assignment not found.")
    _delegation(scope, role_dto(assignment.role).permissions)
    if version != assignment.version or assignment.ended_at is not None:
        raise Conflict()
    assignment.ended_at = timezone.now()
    assignment.version += 1
    assignment.save(update_fields=["ended_at", "version"])
    _event(scope, assignment.role, "role_revoked", reason, assignment=assignment)
    return assignment_dto(assignment)


def project_roles(scope, role_ids=None):
    """Trusted projects adapter lookup; caller owns project authorization."""
    current = resolve_scope(scope.actor_id, scope.organization_id)
    query = (
        OrganizationRole.objects.filter(
            organization_id=current.organization_id, scope_kind="project"
        )
        .prefetch_related("permission_records")
        .order_by("name", "id")
    )
    if role_ids is not None:
        query = query.filter(id__in=role_ids)
    return tuple(role_dto(role) for role in query)


def validate_project_delegation(scope, role_id, project_id=None):
    current = resolve_scope(scope.actor_id, scope.organization_id)
    roles = project_roles(current, [role_id])
    if not roles or roles[0].status != "active":
        raise ValidationError({"role_id": "Choose an active project role in this organization."})
    role = roles[0]
    if "projects.read" not in role.permissions:
        raise ValidationError({"role_id": "Project access roles must include projects.read."})
    if project_id is None:
        _delegation(current, role.permissions)
    else:
        for key in role.permissions:
            authorize(current, key, project_id)
    return role
