"""Public identity lookups; no model instances leave this module."""

from dataclasses import dataclass
from uuid import UUID

from .access import (
    ProjectScopeDTO,
    assign_role,
    authorize,
    create_role,
    get_effective_permissions,
    get_role_permissions,
    has_permission,
    list_assignments,
    list_roles,
    project_roles,
    revoke_assignment,
    update_role,
    validate_project_delegation,
)
from .account import AccountDTO, get_account, update_account
from .models import User

__all__ = [
    "AccountDTO",
    "get_account",
    "update_account",
    "IdentityDTO",
    "get_active_identity",
    "ProjectScopeDTO",
    "project_roles",
    "validate_project_delegation",
    "assign_role",
    "authorize",
    "create_role",
    "get_effective_permissions",
    "get_role_permissions",
    "has_permission",
    "list_assignments",
    "list_roles",
    "revoke_assignment",
    "update_role",
]


@dataclass(frozen=True)
class IdentityDTO:
    id: UUID
    can_provision_organizations: bool


def get_active_identity(user_id=None, *, username=None):
    lookup = {"username": username} if username is not None else {"pk": user_id}
    user = User.objects.filter(**lookup, is_active=True).first()
    if user is None:
        return None
    return IdentityDTO(user.id, user.has_perm("organizations.bootstrap_organization"))
