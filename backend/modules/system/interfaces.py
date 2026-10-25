"""Public system status interface. No ORM objects cross this boundary."""

from dataclasses import dataclass

from django.db import DatabaseError, connection


@dataclass(frozen=True)
class HealthStatus:
    status: str
    service: str = "kaizora-api"
    api_version: str = "v1"


def liveness() -> HealthStatus:
    return HealthStatus(status="ok")


def readiness() -> HealthStatus:
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except DatabaseError:
        return HealthStatus(status="unavailable")
    return HealthStatus(status="ok")
