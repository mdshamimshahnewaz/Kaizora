import pytest
from django.test import Client as AdminClient
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


@pytest.fixture
def clients_setup(django_user_model):
    from modules.organizations.interfaces import create_organization, resolve_scope

    owner = django_user_model.objects.create_superuser(username="clients-owner", password="test")
    org = create_organization(owner.pk, "Clients org", "UTC", owner.pk)
    api = APIClient()
    api.force_authenticate(owner)
    return owner, org, resolve_scope(owner.pk, org.id), api


def test_client_identity_archive_and_conflict(clients_setup):
    from common.api import Conflict
    from modules.clients.interfaces import get_client_summary, lock_active_client
    from modules.clients.models import ClientChangeEvent

    owner, org, scope, api = clients_setup
    base = f"/api/v1/organizations/{org.id}/clients/"
    created = api.post(base, {"code": "Acme", "name": "Acme Ltd"}, format="json")
    assert created.status_code == 201, created.data
    cid = created.data["id"]
    assert api.post(base, {"code": "acME", "name": "Duplicate"}).status_code == 409
    assert (
        api.patch(
            base + cid + "/",
            {"name": "Renamed", "version": 1, "reason": "Trading name"},
            format="json",
        ).status_code
        == 200
    )
    assert (
        api.patch(
            base + cid + "/", {"name": "Stale", "version": 1, "reason": "Old form"}, format="json"
        ).status_code
        == 409
    )
    assert (
        api.patch(
            base + cid + "/",
            {"status": "archived", "version": 2, "reason": "Relationship ended"},
            format="json",
        ).status_code
        == 200
    )
    assert get_client_summary(scope, cid).name == "Renamed"
    with pytest.raises(Conflict):
        lock_active_client(scope, cid)
    assert ClientChangeEvent.objects.filter(client_id=cid).count() == 3
    assert api.get(base + "?ordering=secret").status_code == 400
    assert api.get(base + "?page_size=101").status_code == 400
    assert api.get(base + "?unknown=1").status_code == 400


def test_contacts_permissions_nesting_and_redaction(clients_setup, django_user_model):
    from modules.clients.models import ContactChangeEvent
    from modules.identity.interfaces import assign_role, create_role
    from modules.organizations.interfaces import add_membership, create_organization

    owner, org, scope, api = clients_setup
    base = f"/api/v1/organizations/{org.id}/clients/"
    cid = api.post(base, {"code": "A", "name": "A"}).data["id"]
    other = api.post(base, {"code": "B", "name": "B"}).data["id"]
    contacts = base + cid + "/contacts/"
    contact = api.post(contacts, {"name": "Jane", "email": "jane@example.com"})
    assert contact.status_code == 201, contact.data
    contact_id = contact.data["id"]
    assert (
        api.patch(
            base + other + "/contacts/" + contact_id + "/",
            {"status": "retired", "version": 1, "reason": "Left"},
        ).status_code
        == 404
    )
    assert (
        api.patch(
            contacts + contact_id + "/", {"status": "retired", "version": 1, "reason": "Left"}
        ).status_code
        == 200
    )
    assert api.get(contacts + contact_id + "/").data["status"] == "retired"
    assert api.get(base + other + "/contacts/" + contact_id + "/").status_code == 404
    assert "jane@example.com" not in str(list(ContactChangeEvent.objects.values()))
    user = django_user_model.objects.create_user(username="clients-reader")
    member = add_membership(owner.pk, org.id, user.pk)
    role = create_role(
        owner.pk,
        org.id,
        name="Client reader",
        scope_kind="organization",
        permissions=["clients.read"],
    )
    assign_role(owner.pk, org.id, member.id, role.id, "Read clients")
    api.force_authenticate(user)
    assert api.get(base).status_code == 200
    assert api.get(contacts).status_code == 403
    assert api.get(contacts + contact_id + "/").status_code == 403
    other_org = create_organization(owner.pk, "Other", "UTC", owner.pk)
    assert api.get(f"/api/v1/organizations/{other_org.id}/clients/{cid}/").status_code == 404


def test_admin_client_and_contact_commands(clients_setup):
    from modules.clients.models import Client, Contact

    owner, org, scope, _ = clients_setup
    browser = AdminClient()
    browser.force_login(owner)
    assert (
        browser.post(
            "/admin/clients/client/add/",
            {
                "organization": str(org.id),
                "code": "ADMIN",
                "name": "Admin client",
            },
        ).status_code
        == 302
    )
    client = Client.objects.get(code="ADMIN")
    assert (
        browser.post(
            "/admin/clients/contact/add/",
            {
                "client": str(client.id),
                "name": "Admin contact",
                "email": "contact@example.com",
                "phone": "",
                "position": "",
            },
        ).status_code
        == 302
    )
    contact = Contact.objects.get(client=client)
    assert (
        browser.post(
            f"/admin/clients/contact/{contact.id}/change/",
            {
                "name": contact.name,
                "email": contact.email,
                "phone": "",
                "position": "",
                "status": "retired",
                "version": 1,
                "reason": "Left company",
            },
        ).status_code
        == 302
    )
    contact.refresh_from_db()
    assert contact.version == 2 and contact.status == "retired"
