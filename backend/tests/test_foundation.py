from unittest.mock import patch

import pytest
from django.db import OperationalError
from rest_framework.test import APIClient


def test_public_liveness_contract():
    response = APIClient().get("/api/v1/health/live/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "kaizora-api", "api_version": "v1"}


def test_readiness_does_not_disclose_database_failure():
    with patch(
        "modules.system.interfaces.connection.cursor", side_effect=OperationalError("secret")
    ):
        response = APIClient().get("/api/v1/health/ready/")
    assert response.status_code == 503
    assert response.json()["status"] == "unavailable"
    assert "secret" not in response.content.decode()


@pytest.mark.django_db
def test_postgres_readiness():
    assert APIClient().get("/api/v1/health/ready/").status_code == 200


@pytest.mark.django_db
def test_custom_user_can_authenticate_in_admin(django_user_model):
    user = django_user_model.objects.create_superuser(
        username="foundation-admin", email="admin@example.test", password="test-only-passphrase"
    )
    client = APIClient()
    assert client.login(username=user.username, password="test-only-passphrase")
    assert client.get("/admin/").status_code == 200


def test_business_view_defaults_to_authenticated_access():
    from rest_framework.response import Response
    from rest_framework.test import APIRequestFactory
    from rest_framework.views import APIView

    class PrivateView(APIView):
        def get(self, request):
            return Response({"private": True})

    response = PrivateView.as_view()(APIRequestFactory().get("/private/"))
    assert response.status_code == 403


def test_schema_is_not_public():
    from drf_spectacular.views import SpectacularAPIView
    from rest_framework.test import APIRequestFactory

    response = SpectacularAPIView.as_view()(APIRequestFactory().get("/api/schema/"))
    assert response.status_code == 403
