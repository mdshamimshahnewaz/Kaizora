"""Composition port: feature 0004 may supply a callable; missing policy denies."""

from django.conf import settings
from django.utils.module_loading import import_string
from rest_framework.exceptions import PermissionDenied


def require_permission(scope, permission):
    path = getattr(settings, "ORGANIZATIONS_PERMISSION_POLICY", None)
    if not path or import_string(path)(scope, permission) is not True:
        raise PermissionDenied("Membership management is not available for this account.")
