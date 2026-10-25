"""Clients own writes; other modules consume frozen summaries, never model instances."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from django.db import IntegrityError, connection, transaction
from django.db.models import Q
from rest_framework.exceptions import NotFound, ValidationError

from common.api import Conflict, paginate, reason_text
from modules.identity.interfaces import authorize
from modules.organizations.interfaces import lock_scope, resolve_scope

from .models import Client, ClientChangeEvent, Contact, ContactChangeEvent


@dataclass(frozen=True)
class ClientSummaryDTO:
    id: UUID
    code: str
    name: str
    status: str
    version: int
    created_at: datetime


@dataclass(frozen=True)
class ContactDTO:
    id: UUID
    client_id: UUID
    name: str
    email: str
    phone: str
    position: str
    status: str
    version: int


def _client_dto(client):
    return ClientSummaryDTO(
        client.id, client.code, client.name, client.status, client.version, client.created_at
    )


def _contact_dto(contact):
    return ContactDTO(
        contact.id,
        contact.client_id,
        contact.name,
        contact.email,
        contact.phone,
        contact.position,
        contact.status,
        contact.version,
    )


def _text(value, key, maximum, blank=False):
    if not isinstance(value, str) or len(value) > maximum or (not blank and not value.strip()):
        raise ValidationError({key: f"Provide {'0' if blank else '1'}–{maximum} characters."})
    return value.strip()


def _find_client(organization_id, client_id, lock=False):
    query = Client.objects.select_for_update() if lock else Client.objects
    client = query.filter(pk=client_id, organization_id=organization_id).first()
    if client is None:
        raise NotFound("Client not found.")
    return client


def get_client_summary(scope, client_id, require_active=False):
    """Trusted relationship lookup: caller enforces its own use-case permission.

    Revalidate tenant membership without requiring clients.read for project users.
    Contains no contact data. Archival leaves historical references readable.
    """
    current = resolve_scope(scope.actor_id, scope.organization_id)
    client = _find_client(current.organization_id, client_id)
    if require_active and client.status != Client.Status.ACTIVE:
        raise Conflict("Choose an active client for a new project link.")
    return _client_dto(client)


def get_client_summaries(scope, client_ids):
    """Trusted page hydration: caller supplies at most one bounded page of IDs."""
    current = resolve_scope(scope.actor_id, scope.organization_id)
    ids = tuple(client_ids)
    if len(ids) > 100:
        raise ValidationError({"client_ids": "At most 100 clients per page."})
    return tuple(
        _client_dto(client)
        for client in Client.objects.filter(organization_id=current.organization_id, id__in=ids)
    )


def lock_active_client(scope, client_id):
    """Caller owns transaction and organization lock; lock client until its link commits."""
    if not connection.in_atomic_block:
        raise RuntimeError("lock_active_client requires a transaction.")
    current = resolve_scope(scope.actor_id, scope.organization_id)
    client = _find_client(current.organization_id, client_id, lock=True)
    if client.status != Client.Status.ACTIVE:
        raise Conflict("Choose an active client for a new project link.")
    return _client_dto(client)


def get_client(scope, client_id):
    current = resolve_scope(scope.actor_id, scope.organization_id)
    authorize(current, "clients.read")
    return _client_dto(_find_client(current.organization_id, client_id))


def list_project_client_choices(scope, page=1, page_size=50, search=""):
    """Trusted relationship picker; project caller must authorize creation first."""
    current = resolve_scope(scope.actor_id, scope.organization_id)
    search = _text(search, "search", 100, blank=True)
    query = Client.objects.filter(
        organization_id=current.organization_id, status=Client.Status.ACTIVE
    )
    if search:
        query = query.filter(Q(name__icontains=search) | Q(code__icontains=search))
    return paginate(query.order_by("name", "id"), page, page_size, _client_dto)


def list_clients(scope, page=1, page_size=50, search="", status=None, ordering="name"):
    current = resolve_scope(scope.actor_id, scope.organization_id)
    authorize(current, "clients.read")
    search = _text(search, "search", 100, blank=True)
    if ordering not in {"name", "-name", "code", "-code"}:
        raise ValidationError({"ordering": "Choose name, -name, code or -code."})
    query = Client.objects.filter(organization_id=current.organization_id)
    if status is not None:
        if status not in Client.Status.values:
            raise ValidationError({"status": "Unknown client status."})
        query = query.filter(status=status)
    if search:
        query = query.filter(Q(name__icontains=search) | Q(code__icontains=search))
    return paginate(query.order_by(ordering, "id"), page, page_size, _client_dto)


def _event(entity, actor_id, reason, fields, before=0):
    model, key = (
        (ClientChangeEvent, "client")
        if isinstance(entity, Client)
        else (ContactChangeEvent, "contact")
    )
    model.objects.create(
        **{key: entity},
        organization_id=entity.organization_id,
        actor_id=actor_id,
        action="updated" if before else "created",
        reason=reason,
        changed_fields=sorted(fields),
        before_version=before,
        after_version=entity.version,
    )


@transaction.atomic
def create_client(scope, code, name):
    _, current = lock_scope(scope.actor_id, scope.organization_id)
    authorize(current, "clients.manage")
    code = _text(code, "code", 32)
    name = _text(name, "name", 200)
    normalized = code.casefold()
    if len(normalized) > 32:
        raise ValidationError({"code": "Normalized code exceeds 32 characters."})
    try:
        with transaction.atomic():
            client = Client.objects.create(
                organization_id=current.organization_id,
                code=code,
                normalized_code=normalized,
                name=name,
            )
    except IntegrityError:
        raise Conflict("A client with this code already exists in this organization.") from None
    _event(client, current.actor_id, "Client created", ["code", "name"])
    return _client_dto(client)


@transaction.atomic
def update_client(scope, client_id, *, version, reason, **changes):
    _, current = lock_scope(scope.actor_id, scope.organization_id)
    authorize(current, "clients.manage")
    client = _find_client(current.organization_id, client_id, lock=True)
    if client.version != version:
        raise Conflict()
    reason = reason_text(reason)
    if not changes or set(changes) - {"name", "status"}:
        raise ValidationError({"detail": "Provide name and/or status; code is immutable."})
    if "name" in changes:
        changes["name"] = _text(changes["name"], "name", 200)
    if "status" in changes and changes["status"] not in Client.Status.values:
        raise ValidationError({"status": "Unknown client status."})
    fields = [key for key, value in changes.items() if getattr(client, key) != value]
    if not fields:
        return _client_dto(client)
    for key in fields:
        setattr(client, key, changes[key])
    before = client.version
    client.version += 1
    client.save(update_fields=[*fields, "version"])
    _event(client, current.actor_id, reason, fields, before)
    return _client_dto(client)


def list_contacts(scope, client_id, page=1, page_size=50, status=None):
    current = resolve_scope(scope.actor_id, scope.organization_id)
    authorize(current, "contacts.read")
    client = _find_client(current.organization_id, client_id)
    query = Contact.objects.filter(client=client, organization_id=current.organization_id)
    if status is not None:
        if status not in Contact.Status.values:
            raise ValidationError({"status": "Unknown contact status."})
        query = query.filter(status=status)
    return paginate(query.order_by("name", "id"), page, page_size, _contact_dto)


def get_contact(scope, client_id, contact_id):
    current = resolve_scope(scope.actor_id, scope.organization_id)
    authorize(current, "contacts.read")
    _find_client(current.organization_id, client_id)
    contact = Contact.objects.filter(
        pk=contact_id, client_id=client_id, organization_id=current.organization_id
    ).first()
    if contact is None:
        raise NotFound("Contact not found.")
    return _contact_dto(contact)


def _contact_fields(changes):
    for field, maximum in {"name": 200, "email": 254, "phone": 50, "position": 200}.items():
        if field in changes:
            changes[field] = _text(changes[field], field, maximum, blank=field != "name")
    if changes.get("email"):
        try:
            validate_email(changes["email"])
        except DjangoValidationError:
            raise ValidationError({"email": "Enter a valid email address."}) from None
    if "status" in changes and changes["status"] not in Contact.Status.values:
        raise ValidationError({"status": "Unknown contact status."})
    return changes


@transaction.atomic
def create_contact(scope, client_id, name, email="", phone="", position=""):
    _, current = lock_scope(scope.actor_id, scope.organization_id)
    authorize(current, "contacts.manage")
    client = _find_client(current.organization_id, client_id, lock=True)
    if client.status != Client.Status.ACTIVE:
        raise Conflict("Restore the client before adding contacts.")
    fields = _contact_fields(dict(name=name, email=email, phone=phone, position=position))
    contact = Contact.objects.create(
        organization_id=current.organization_id, client=client, **fields
    )
    _event(contact, current.actor_id, "Contact created", fields)
    return _contact_dto(contact)


@transaction.atomic
def update_contact(scope, client_id, contact_id, *, version, reason, **changes):
    _, current = lock_scope(scope.actor_id, scope.organization_id)
    authorize(current, "contacts.manage")
    _find_client(current.organization_id, client_id, lock=True)
    contact = (
        Contact.objects.select_for_update()
        .filter(pk=contact_id, client_id=client_id, organization_id=current.organization_id)
        .first()
    )
    if contact is None:
        raise NotFound("Contact not found.")
    if contact.version != version:
        raise Conflict()
    reason = reason_text(reason)
    if not changes or set(changes) - {"name", "email", "phone", "position", "status"}:
        raise ValidationError({"detail": "Provide contact fields to update."})
    changes = _contact_fields(changes)
    fields = [key for key, value in changes.items() if getattr(contact, key) != value]
    if not fields:
        return _contact_dto(contact)
    for key in fields:
        setattr(contact, key, changes[key])
    before = contact.version
    contact.version += 1
    contact.save(update_fields=[*fields, "version"])
    _event(contact, current.actor_id, reason, fields, before)
    return _contact_dto(contact)
