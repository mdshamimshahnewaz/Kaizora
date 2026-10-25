import pytest
from rest_framework.exceptions import ValidationError

from common.api import Conflict

pytestmark = pytest.mark.django_db


def test_account_atomic_update_and_stale_guard(django_user_model):
    from modules.identity.account import get_account, update_account

    user = django_user_model.objects.create_user(username="account", email="a@example.com")
    assert get_account(user.pk).version == 1
    saved = update_account(user.pk, 1, first_name="A", preferences={"theme": "dark"})
    assert saved.display_name == "A" and saved.version == 2
    with pytest.raises(Conflict):
        update_account(user.pk, 1, first_name="Overwrite")
    with pytest.raises(ValidationError):
        update_account(user.pk, 2, first_name="Invalid", preferences={"timezone": "invalid"})
    assert get_account(user.pk).first_name == "A"
    assert get_account(user.pk).email == "a@example.com"


def test_account_api_self_scope_and_csrf(django_user_model):
    from rest_framework.test import APIClient

    user = django_user_model.objects.create_user(username="account")
    client = APIClient(enforce_csrf_checks=True)
    assert client.get("/api/v1/account/me/").status_code == 403
    client.force_login(user)
    assert client.patch("/api/v1/account/me/", {"version": 1}, format="json").status_code == 403
    client.force_authenticate(user)
    assert client.get("/api/v1/account/me/").json()["username"] == "account"
    assert (
        client.patch(
            "/api/v1/account/me/", {"version": 1, "is_staff": True}, format="json"
        ).status_code
        == 400
    )
    assert client.get("/api/v1/account/me/?user_id=another").status_code == 400


def test_account_timezone_inheritance_and_admin_revision(django_user_model):
    from django.test import Client

    from modules.identity.account import get_account, update_account
    from modules.identity.models import AccountChangeEvent, AccountPreferences
    from modules.organizations.interfaces import create_organization

    user = django_user_model.objects.create_superuser(username="operator", password="test")
    org = create_organization(user.pk, "Timezone", "America/New_York", user.pk)
    assert get_account(user.pk, org.id).effective_timezone == "America/New_York"
    update_account(user.pk, 1, preferences={"timezone": "UTC"})
    assert get_account(user.pk, org.id).effective_timezone == "UTC"
    client = Client()
    client.force_login(user)
    response = client.post(
        f"/admin/identity/accountpreferences/{user.pk}/change/",
        {
            "theme": "dark",
            "timezone": "Asia/Dhaka",
            "version": 2,
        },
    )
    assert response.status_code == 302
    assert AccountPreferences.objects.get(user=user).version == 3
    response = client.post(
        f"/admin/identity/user/{user.pk}/change/",
        {
            "username": "operator",
            "first_name": "Admin name",
            "last_name": "",
            "email": "",
            "is_active": "on",
            "is_staff": "on",
            "is_superuser": "on",
            "date_joined_0": "2026-10-18",
            "date_joined_1": "10:00:00",
            "account_version": 3,
        },
    )
    assert response.status_code == 302
    assert get_account(user.pk).version == 4
    assert get_account(user.pk).first_name == "Admin name"
    assert AccountChangeEvent.objects.filter(user=user).count() == 3
    stale = client.post(
        f"/admin/identity/user/{user.pk}/change/",
        {
            "username": "operator",
            "first_name": "Stale name",
            "last_name": "",
            "email": "",
            "is_active": "on",
            "is_staff": "on",
            "is_superuser": "on",
            "date_joined_0": "2026-10-18",
            "date_joined_1": "10:00:00",
            "account_version": 3,
        },
    )
    assert stale.status_code == 200
    assert b"changed since" in stale.content
    assert get_account(user.pk).first_name == "Admin name"
    assert get_account(user.pk).version == 4
