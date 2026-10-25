"""Public commands/queries. All authority is revalidated against current membership."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils.module_loading import import_string
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from common.api import Conflict
from common.api import paginate as _page
from common.api import reason_text as _reason

from .models import Membership, MembershipStatusEvent, Organization, OrganizationChangeEvent
from .policy import require_permission


def get_active_identity(user_id=None, username=None):
    return import_string(settings.ORGANIZATIONS_IDENTITY_LOOKUP)(user_id, username=username)


@dataclass(frozen=True)
class ActiveScopeDTO:
    actor_id: UUID
    organization_id: UUID
    membership_id: UUID
    is_owner: bool


@dataclass(frozen=True)
class OrganizationDTO:
    id: UUID
    name: str
    timezone: str
    status: str
    version: int
    membership_id: UUID | None
    is_owner: bool


@dataclass(frozen=True)
class MembershipDTO:
    id: UUID
    user_id: UUID
    status: str
    is_owner: bool
    version: int
    joined_at: datetime
    username: str
    display_name: str


def _org_dto(org, membership=None):
    return OrganizationDTO(
        org.id,
        org.name,
        org.timezone,
        org.status,
        org.version,
        membership.id if membership else None,
        membership.is_owner if membership else False,
    )


def _member_dto(member):
    return MembershipDTO(
        member.id,
        member.user_id,
        member.status,
        member.is_owner,
        member.version,
        member.joined_at,
        member.user.get_username(),
        member.user.get_full_name(),
    )


def resolve_scope(actor_id, organization_id):
    member = Membership.objects.filter(
        user_id=actor_id,
        user__is_active=True,
        organization_id=organization_id,
        organization__status="active",
        status="active",
    ).first()
    if member is None:
        raise NotFound("Organization not found.")
    return ActiveScopeDTO(member.user_id, member.organization_id, member.id, member.is_owner)


def list_my_organizations(actor_id, page=1, page_size=50):
    if get_active_identity(actor_id) is None:
        raise PermissionDenied()
    query = (
        Membership.objects.filter(user_id=actor_id, status="active", organization__status="active")
        .select_related("organization")
        .order_by("organization__name", "organization_id")
    )
    return _page(query, page, page_size, lambda m: _org_dto(m.organization, m))


def get_organization(actor_id, organization_id):
    scope = resolve_scope(actor_id, organization_id)
    return _org_dto(
        Organization.objects.get(pk=scope.organization_id),
        Membership.objects.get(pk=scope.membership_id),
    )


def _event(member, actor_id, reason, before_status="", before_owner=False):
    MembershipStatusEvent.objects.create(
        membership=member,
        actor_id=actor_id,
        reason=reason,
        before_status=before_status,
        after_status=member.status,
        before_owner=before_owner,
        after_owner=member.is_owner,
    )


@transaction.atomic
def create_organization(actor_id, name, timezone, owner_user_id=None, owner_username=None):
    actor = get_active_identity(actor_id)
    if actor is None or not actor.can_provision_organizations:
        raise PermissionDenied("Organization provisioning requires operator permission.")
    if not isinstance(name, str) or not name.strip() or len(name) > 200:
        raise ValidationError({"name": "Provide a name of 1–200 characters."})
    try:
        ZoneInfo(timezone)
    except (ZoneInfoNotFoundError, ValueError, TypeError):
        raise ValidationError({"timezone": "Use a valid IANA timezone."}) from None
    if (owner_user_id is None) == (owner_username is None):
        raise ValidationError({"owner_user_id": "Provide exactly one owner ID or username."})
    owner_identity = get_active_identity(owner_user_id, username=owner_username)
    if owner_identity is None:
        raise ValidationError({"owner_user_id": "Choose an active existing user."})
    owner_user_id = owner_identity.id
    org = Organization.objects.create(name=name.strip(), timezone=timezone)
    owner = Membership.objects.create(organization=org, user_id=owner_user_id, is_owner=True)
    _event(owner, actor_id, "Organization provisioned")
    OrganizationChangeEvent.objects.create(
        organization=org,
        actor_id=actor_id,
        action="created",
        reason="Organization provisioned",
        after_version=1,
    )
    # Operator permission provisions a tenant; it never grants read membership.
    return _org_dto(org, owner if owner.user_id == actor.id else None)


def list_memberships(actor_id, organization_id, page=1, page_size=50, status=None):
    scope = resolve_scope(actor_id, organization_id)
    require_permission(scope, "memberships.read")
    query = (
        Membership.objects.filter(organization_id=scope.organization_id)
        .select_related("user")
        .order_by("id")
    )
    if status is not None:
        if status not in Membership.Status.values:
            raise ValidationError({"status": "Unknown membership status."})
        query = query.filter(status=status)
    return _page(query, page, page_size, _member_dto)


def get_membership(scope, membership_id):
    current = resolve_scope(scope.actor_id, scope.organization_id)
    require_permission(current, "memberships.read")
    member = Membership.objects.filter(
        pk=membership_id, organization_id=current.organization_id
    ).first()
    if member is None:
        raise NotFound()
    return _member_dto(member)


def lock_scope(actor_id, organization_id):
    # All membership/owner commands lock the organization before resolving authority.
    # A queued command therefore observes a preceding committed revocation.
    org = Organization.objects.select_for_update().filter(pk=organization_id).first()
    if org is None:
        raise NotFound("Organization not found.")
    return org, resolve_scope(actor_id, organization_id)


@transaction.atomic
def add_membership(actor_id, organization_id, user_id=None, username=None):
    org, scope = lock_scope(actor_id, organization_id)
    require_permission(scope, "memberships.manage")
    if (user_id is None) == (username is None):
        raise ValidationError({"user_id": "Provide exactly one user ID or username."})
    identity = get_active_identity(user_id, username=username)
    if identity is None:
        raise ValidationError({"user_id": "Choose an active existing user."})
    user_id = identity.id
    if Membership.objects.filter(organization=org, user_id=user_id).exists():
        raise Conflict("Membership already exists. Reactivate the existing membership instead.")
    member = Membership.objects.create(organization=org, user_id=user_id)
    _event(member, actor_id, "Membership added")
    return _member_dto(member)


@transaction.atomic
def change_membership(actor_id, organization_id, membership_id, status, version, reason):
    org, scope = lock_scope(actor_id, organization_id)
    require_permission(scope, "memberships.manage")
    reason = _reason(reason)
    if status not in Membership.Status.values:
        raise ValidationError({"status": "Unknown membership status."})
    member = Membership.objects.filter(pk=membership_id, organization=org).first()
    if member is None:
        raise NotFound()
    if member.version != version:
        raise Conflict()
    if status == "active" and get_active_identity(member.user_id) is None:
        raise Conflict("An inactive user cannot have membership reactivated.")
    if member.is_owner and not scope.is_owner:
        raise PermissionDenied("Only an owner can change another owner’s access.")
    if member.is_owner and status != "active":
        other_owner = (
            Membership.objects.filter(
                organization=org, is_owner=True, status="active", user__is_active=True
            )
            .exclude(pk=member.pk)
            .exists()
        )
        if not other_owner:
            raise Conflict("Transfer ownership before suspending or ending the last owner.")
    if member.status == status:
        return _member_dto(member)
    before = member.status
    member.status = status
    member.version += 1
    member.save(update_fields=["status", "version"])
    _event(member, actor_id, reason, before, member.is_owner)
    return _member_dto(member)


@transaction.atomic
def transfer_owner(actor_id, organization_id, target_membership_id, version, reason):
    org, scope = lock_scope(actor_id, organization_id)
    if not scope.is_owner:
        raise PermissionDenied("Only an active owner can transfer ownership.")
    reason = _reason(reason)
    if org.version != version:
        raise Conflict()
    target = Membership.objects.filter(
        pk=target_membership_id, organization=org, status="active", user__is_active=True
    ).first()
    if target is None:
        raise ValidationError(
            {"target_membership_id": "Choose an active member of this organization."}
        )
    if target.pk == scope.membership_id:
        raise Conflict("Choose another member.")
    source = Membership.objects.get(pk=scope.membership_id)
    for member, is_owner in [(target, True), (source, False)]:
        previous_owner = member.is_owner
        member.is_owner = is_owner
        member.version += 1
        member.save(update_fields=["is_owner", "version"])
        _event(member, actor_id, reason, member.status, previous_owner)
    previous_version = org.version
    org.version += 1
    org.save(update_fields=["version"])
    OrganizationChangeEvent.objects.create(
        organization=org,
        actor_id=actor_id,
        action="owner_transferred",
        reason=reason,
        before_version=previous_version,
        after_version=org.version,
    )
    return _org_dto(org, source)


def resolve_assignment_target(scope, membership_id):
    """Identity may validate a grant target without requiring memberships.read."""
    current = resolve_scope(scope.actor_id, scope.organization_id)
    member = Membership.objects.filter(
        pk=membership_id,
        organization_id=current.organization_id,
        status="active",
        user__is_active=True,
    ).first()
    if member is None:
        raise NotFound("Active membership not found.")
    return member.id


@dataclass(frozen=True)
class AssignmentTargetDTO:
    id: UUID
    username: str
    display_name: str
    status: str


def _assignment_target(member):
    return AssignmentTargetDTO(
        member.id, member.user.get_username(), member.user.get_full_name(), member.status
    )


def list_assignment_targets(scope, page=1, page_size=50, search=""):
    """Trusted assignment picker; caller enforces its owning use-case permission."""
    current = resolve_scope(scope.actor_id, scope.organization_id)
    if not isinstance(search, str) or len(search) > 100:
        raise ValidationError({"search": "Maximum 100 characters."})
    query = Membership.objects.filter(
        organization_id=current.organization_id, status="active", user__is_active=True
    ).select_related("user")
    if search.strip():
        query = query.filter(
            Q(user__username__icontains=search.strip())
            | Q(user__first_name__icontains=search.strip())
            | Q(user__last_name__icontains=search.strip())
        )
    return _page(query.order_by("user__username", "id"), page, page_size, _assignment_target)


def get_assignment_target_summary(scope, membership_id):
    """Trusted historical label lookup; does not grant assignment eligibility."""
    current = resolve_scope(scope.actor_id, scope.organization_id)
    member = (
        Membership.objects.select_related("user")
        .filter(pk=membership_id, organization_id=current.organization_id)
        .first()
    )
    if member is None:
        raise NotFound("Membership not found.")
    return _assignment_target(member)


def get_assignment_target_summaries(scope, membership_ids):
    """Trusted bounded historical labels; caller enforces its owning read permission."""
    current = resolve_scope(scope.actor_id, scope.organization_id)
    ids = tuple(membership_ids)
    if len(ids) > 100:
        raise ValidationError({"membership_ids": "At most 100 members per page."})
    return tuple(
        _assignment_target(member)
        for member in Membership.objects.select_related("user").filter(
            organization_id=current.organization_id, id__in=ids
        )
    )


def provisioning_capability(actor_id):
    identity = get_active_identity(actor_id)
    return identity is not None and identity.can_provision_organizations


def authorized_organization_ids(actor_id, permission=None):
    """Current organization scopes available to server-side administration adapters."""
    ids = Membership.objects.filter(
        user_id=actor_id, user__is_active=True, status="active", organization__status="active"
    ).values_list("organization_id", flat=True)
    allowed = []
    for org_id in ids:
        try:
            scope = resolve_scope(actor_id, org_id)
            if permission:
                require_permission(scope, permission)
            allowed.append(org_id)
        except (PermissionDenied, NotFound):
            continue
    return tuple(allowed)
