from dataclasses import dataclass
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.conf import settings
from django.db import transaction
from rest_framework.exceptions import PermissionDenied, ValidationError

from common.api import Conflict
from modules.organizations.interfaces import get_organization

from .models import AccountChangeEvent, AccountPreferences, User


@dataclass(frozen=True)
class PreferencesDTO:
    theme: str | None
    timezone: str | None


@dataclass(frozen=True)
class AccountDTO:
    id: UUID
    username: str
    email: str
    first_name: str
    last_name: str
    display_name: str
    preferences: PreferencesDTO
    version: int
    effective_timezone: str


def _dto(user, preferences, organization=None):
    inherited = (
        get_organization(user.pk, organization).timezone if organization else settings.TIME_ZONE
    )
    return AccountDTO(
        user.pk,
        user.username,
        user.email,
        user.first_name,
        user.last_name,
        user.get_full_name() or user.username,
        PreferencesDTO(preferences.theme, preferences.timezone),
        preferences.version,
        preferences.timezone or inherited,
    )


def get_account(actor_id, organization=None):
    user = User.objects.filter(pk=actor_id, is_active=True).first()
    if user is None:
        raise PermissionDenied()
    preferences = AccountPreferences.objects.filter(user=user).first() or AccountPreferences(
        user=user
    )
    return _dto(user, preferences, organization)


@transaction.atomic
def update_account(
    actor_id, version, *, first_name=None, last_name=None, preferences=None, target_user_id=None
):
    actor = User.objects.get(pk=actor_id)
    if not actor.is_active:
        raise PermissionDenied()
    if target_user_id is not None and target_user_id != actor.pk:
        if not actor.is_staff or not actor.has_perm("identity.change_user"):
            raise PermissionDenied()
    user = User.objects.select_for_update().get(pk=target_user_id or actor_id)
    stored, _ = AccountPreferences.objects.get_or_create(user=user)
    if stored.version != version:
        raise Conflict()
    changed = []
    for field, value in (("first_name", first_name), ("last_name", last_name)):
        if value is not None:
            if not isinstance(value, str) or len(value) > 150:
                raise ValidationError({field: "Use at most 150 characters."})
            if getattr(user, field) != value:
                setattr(user, field, value)
                changed.append(field)
    preferences = preferences or {}
    if set(preferences) - {"theme", "timezone"}:
        raise ValidationError({"preferences": "Unknown field."})
    if "theme" in preferences and preferences["theme"] not in (None, "light", "dark", "system"):
        raise ValidationError({"theme": "Choose light, dark or system."})
    if preferences.get("timezone") is not None:
        try:
            ZoneInfo(preferences["timezone"])
        except (ZoneInfoNotFoundError, ValueError, TypeError):
            raise ValidationError({"timezone": "Choose a valid IANA timezone."}) from None
    for field, value in preferences.items():
        if getattr(stored, field) != value:
            setattr(stored, field, value)
            changed.append(field)
    user.save(update_fields=["first_name", "last_name"])
    stored.version += 1
    stored.save()
    AccountChangeEvent.objects.create(
        actor=actor, user=user, version=stored.version, changed_fields=changed
    )
    return _dto(user, stored)
