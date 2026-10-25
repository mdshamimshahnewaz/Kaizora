from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from common.api import ERRORS, PAGE_PARAMS, page_parameters, page_response, validated
from modules.organizations.interfaces import resolve_scope

from .. import interfaces as service
from ..catalog import ALL_KEYS, PRESETS, PROJECT_KEYS
from .access_serializers import (
    AssignmentPageSerializer,
    AssignmentSerializer,
    AssignRoleSerializer,
    CatalogSerializer,
    CreateRoleSerializer,
    PermissionsSerializer,
    RevokeSerializer,
    RolePageSerializer,
    RoleSerializer,
    UpdateRoleSerializer,
)


@method_decorator(never_cache, name="dispatch")
class PermissionsView(APIView):
    @extend_schema(responses={200: PermissionsSerializer, **ERRORS})
    def get(self, request, org):
        scope = resolve_scope(request.user.pk, org)
        return Response(PermissionsSerializer(service.get_effective_permissions(scope)).data)


@method_decorator(never_cache, name="dispatch")
class CatalogView(APIView):
    @extend_schema(responses={200: CatalogSerializer, **ERRORS})
    def get(self, request, org):
        resolve_scope(request.user.pk, org)
        return Response(
            CatalogSerializer(
                {
                    "entries": [
                        {"key": key, "scope": "project" if key in PROJECT_KEYS else "organization"}
                        for key in sorted(ALL_KEYS)
                    ],
                    "presets": PRESETS,
                }
            ).data
        )


@method_decorator(never_cache, name="dispatch")
class RolesView(APIView):
    @extend_schema(parameters=PAGE_PARAMS, responses={200: RolePageSerializer, **ERRORS})
    def get(self, request, org):
        page, size = page_parameters(request)
        return page_response(
            request,
            page,
            size,
            service.list_roles(request.user.pk, org, page, size),
            RoleSerializer,
        )

    @extend_schema(request=CreateRoleSerializer, responses={201: RoleSerializer, **ERRORS})
    def post(self, request, org):
        result = service.create_role(
            request.user.pk, org, **validated(CreateRoleSerializer, request)
        )
        return Response(RoleSerializer(result).data, status=201)


class RoleView(APIView):
    @extend_schema(request=UpdateRoleSerializer, responses={200: RoleSerializer, **ERRORS})
    def patch(self, request, org, role):
        result = service.update_role(
            request.user.pk, org, role, **validated(UpdateRoleSerializer, request)
        )
        return Response(RoleSerializer(result).data)


@method_decorator(never_cache, name="dispatch")
class AssignmentsView(APIView):
    @extend_schema(parameters=PAGE_PARAMS, responses={200: AssignmentPageSerializer, **ERRORS})
    def get(self, request, org):
        page, size = page_parameters(request)
        return page_response(
            request,
            page,
            size,
            service.list_assignments(request.user.pk, org, page, size),
            AssignmentSerializer,
        )

    @extend_schema(request=AssignRoleSerializer, responses={201: AssignmentSerializer, **ERRORS})
    def post(self, request, org):
        result = service.assign_role(
            request.user.pk, org, **validated(AssignRoleSerializer, request)
        )
        return Response(AssignmentSerializer(result).data, status=201)


class RevokeView(APIView):
    @extend_schema(request=RevokeSerializer, responses={200: AssignmentSerializer, **ERRORS})
    def post(self, request, org, assignment):
        result = service.revoke_assignment(
            request.user.pk, org, assignment, **validated(RevokeSerializer, request)
        )
        return Response(AssignmentSerializer(result).data)
