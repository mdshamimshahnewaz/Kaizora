import pytest
from django.core.cache import cache
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db
PASSWORD = "test-only-long-passphrase"


@pytest.fixture(autouse=True)
def clear_throttle():
    cache.clear()


@pytest.fixture
def user(django_user_model):
    return django_user_model.objects.create_user(
        username="member", password=PASSWORD, first_name="Test", last_name="Member"
    )


def csrf(client):
    response = client.get("/api/v1/auth/session/")
    assert response.status_code == 200
    assert "no-store" in response["Cache-Control"]
    return response.json()["csrf_token"]


def sign_in(client, password=PASSWORD):
    return client.post(
        "/api/v1/auth/login/",
        {"username": "member", "password": password},
        format="json",
        HTTP_X_CSRFTOKEN=csrf(client),
    )


def test_session_login_logout_and_revoked_cookie(user):
    client = APIClient(enforce_csrf_checks=True)
    assert client.get("/api/v1/auth/session/").json()["user"] is None
    response = sign_in(client)
    assert response.status_code == 200
    assert response.json()["user"] == {
        "id": str(user.id),
        "username": "member",
        "display_name": "Test Member",
        "email": "",
    }
    assert "password" not in response.json()["user"]
    old_cookie = client.cookies["sessionid"].value
    assert client.cookies["sessionid"]["httponly"]
    assert client.get("/api/v1/auth/session/").json()["user"]["id"] == str(user.id)
    response = client.post("/api/v1/auth/logout/", HTTP_X_CSRFTOKEN=csrf(client))
    assert response.status_code == 204
    client.cookies["sessionid"] = old_cookie
    assert client.get("/api/v1/auth/session/").json()["user"] is None


def test_login_and_logout_require_csrf_even_anonymously(user):
    client = APIClient(enforce_csrf_checks=True)
    for path in ["login", "logout"]:
        assert client.post(f"/api/v1/auth/{path}/", {}, format="json").status_code == 403
    assert sign_in(client).status_code == 200
    assert client.post("/api/v1/auth/logout/").status_code == 403
    assert client.get("/api/v1/auth/session/").json()["user"] is not None


def test_login_rotates_csrf_and_session_key(user):
    client = APIClient(enforce_csrf_checks=True)
    session = client.session
    session["anonymous"] = True
    session.save()
    client.cookies["sessionid"] = session.session_key
    old_key = session.session_key
    old_csrf = csrf(client)
    assert sign_in(client).status_code == 200
    assert client.cookies["sessionid"].value != old_key
    assert client.post("/api/v1/auth/logout/", HTTP_X_CSRFTOKEN=old_csrf).status_code == 403


def test_invalid_and_inactive_users_share_generic_error(user):
    client = APIClient(enforce_csrf_checks=True)
    invalid = sign_in(client, "incorrect")
    user.is_active = False
    user.save(update_fields=["is_active"])
    inactive = sign_in(client)
    user.delete()
    missing = sign_in(client)
    assert invalid.status_code == inactive.status_code == missing.status_code == 400
    assert invalid.json() == inactive.json() == missing.json()
    assert client.get("/api/v1/auth/session/").json()["user"] is None


def test_login_throttled():
    client = APIClient(enforce_csrf_checks=True)
    token = csrf(client)
    for _ in range(10):
        assert (
            client.post(
                "/api/v1/auth/login/", {}, format="json", HTTP_X_CSRFTOKEN=token
            ).status_code
            == 400
        )
    assert (
        client.post("/api/v1/auth/login/", {}, format="json", HTTP_X_CSRFTOKEN=token).status_code
        == 429
    )


def test_logout_idempotent_and_get_not_allowed():
    client = APIClient(enforce_csrf_checks=True)
    assert client.post("/api/v1/auth/logout/", HTTP_X_CSRFTOKEN=csrf(client)).status_code == 204
    assert client.get("/api/v1/auth/logout/").status_code == 405


def test_deactivated_session_is_anonymous(user):
    client = APIClient(enforce_csrf_checks=True)
    assert sign_in(client).status_code == 200
    user.is_active = False
    user.save(update_fields=["is_active"])
    assert client.get("/api/v1/auth/session/").json()["user"] is None


def test_auth_csrf_errors_are_json_and_admin_keeps_default_error_page():
    client = APIClient(enforce_csrf_checks=True)
    response = client.post("/api/v1/auth/login/", {}, format="json")
    assert response.status_code == 403
    assert response.json() == {"detail": "CSRF verification failed. Refresh and try again."}
    admin_response = client.post("/admin/login/", {})
    assert admin_response.status_code == 403
    assert admin_response["Content-Type"].startswith("text/html")
