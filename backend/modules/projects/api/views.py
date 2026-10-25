from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from common.api import ERRORS, PAGE_PARAMS, PageDTO, page_parameters, page_response, validated
from modules.organizations.interfaces import resolve_scope

from .. import interfaces as service
from .serializers import (
    CreateProjectSerializer,
    EndProjectAccessSerializer,
    GrantProjectAccessSerializer,
    ProjectAccessPageSerializer,
    ProjectAccessSerializer,
    ProjectOptionPageSerializer,
    ProjectOptionSerializer,
    ProjectPageSerializer,
    ProjectSerializer,
    TransitionProjectSerializer,
    UpdateProjectSerializer,
)


@method_decorator(never_cache, name="dispatch")
class ProjectsView(APIView):
    @extend_schema(
        parameters=[
            *PAGE_PARAMS,
            *[
                OpenApiParameter(key, str)
                for key in ("search", "status", "type", "client_id", "ordering")
            ],
        ],
        responses={200: ProjectPageSerializer, **ERRORS},
        operation_id="projects_list",
    )
    def get(self, request, org):
        keys = ("search", "status", "type", "client_id", "ordering")
        page, size = page_parameters(request, keys)
        result = service.list_projects(
            resolve_scope(request.user.pk, org),
            page,
            size,
            **{key: request.query_params[key] for key in keys if key in request.query_params},
        )
        return page_response(request, page, size, result, ProjectSerializer)

    @extend_schema(request=CreateProjectSerializer, responses={201: ProjectSerializer, **ERRORS})
    def post(self, request, org):
        result = service.create_project(
            resolve_scope(request.user.pk, org), **validated(CreateProjectSerializer, request)
        )
        return Response(ProjectSerializer(result).data, status=201)


@method_decorator(never_cache, name="dispatch")
class ProjectView(APIView):
    @extend_schema(responses={200: ProjectSerializer, **ERRORS})
    def get(self, request, org, project):
        return Response(
            ProjectSerializer(
                service.get_project(resolve_scope(request.user.pk, org), project)
            ).data
        )

    @extend_schema(request=UpdateProjectSerializer, responses={200: ProjectSerializer, **ERRORS})
    def patch(self, request, org, project):
        return Response(
            ProjectSerializer(
                service.update_project(
                    resolve_scope(request.user.pk, org),
                    project,
                    **validated(UpdateProjectSerializer, request),
                )
            ).data
        )


@method_decorator(never_cache, name="dispatch")
class ProjectTransitionView(APIView):
    @extend_schema(
        request=TransitionProjectSerializer, responses={200: ProjectSerializer, **ERRORS}
    )
    def post(self, request, org, project):
        return Response(
            ProjectSerializer(
                service.transition_project(
                    resolve_scope(request.user.pk, org),
                    project,
                    **validated(TransitionProjectSerializer, request),
                )
            ).data
        )


@method_decorator(never_cache, name="dispatch")
class ProjectAccessView(APIView):
    @extend_schema(
        parameters=PAGE_PARAMS,
        responses={200: ProjectAccessPageSerializer, **ERRORS},
        operation_id="projects_access_list",
    )
    def get(self, request, org, project):
        page, size = page_parameters(request)
        result = service.list_access(resolve_scope(request.user.pk, org), project, page, size)
        return page_response(request, page, size, result, ProjectAccessSerializer)

    @extend_schema(
        request=GrantProjectAccessSerializer, responses={201: ProjectAccessSerializer, **ERRORS}
    )
    def post(self, request, org, project):
        result = service.grant_access(
            resolve_scope(request.user.pk, org),
            project,
            **validated(GrantProjectAccessSerializer, request),
        )
        return Response(ProjectAccessSerializer(result).data, status=201)


@method_decorator(never_cache, name="dispatch")
class ProjectAccessEndView(APIView):
    @extend_schema(
        request=EndProjectAccessSerializer, responses={200: ProjectAccessSerializer, **ERRORS}
    )
    def post(self, request, org, project, grant):
        result = service.end_access(
            resolve_scope(request.user.pk, org),
            project,
            grant,
            **validated(EndProjectAccessSerializer, request),
        )
        return Response(ProjectAccessSerializer(result).data)


@method_decorator(never_cache, name="dispatch")
class ProjectOptionsView(APIView):
    @extend_schema(
        parameters=[
            *PAGE_PARAMS,
            OpenApiParameter("kind", str, required=True),
            OpenApiParameter("search", str),
        ],
        responses={200: ProjectOptionPageSerializer, **ERRORS},
        operation_id="projects_options_list",
    )
    def get(self, request, org, project=None):
        page, size = page_parameters(request, ("kind", "search"))
        result = service.assignment_options(
            resolve_scope(request.user.pk, org),
            request.query_params.get("kind"),
            page,
            size,
            request.query_params.get("search", ""),
            project,
        )
        options = tuple(
            {
                "id": item.id,
                "label": (item.display_name or item.username)
                if hasattr(item, "username")
                else item.name,
            }
            for item in result.results
        )
        return page_response(
            request, page, size, PageDTO(result.count, options), ProjectOptionSerializer
        )


class ProjectAccessOptionsView(ProjectOptionsView):
    @extend_schema(
        parameters=[
            *PAGE_PARAMS,
            OpenApiParameter("kind", str, required=True),
            OpenApiParameter("search", str),
        ],
        responses={200: ProjectOptionPageSerializer, **ERRORS},
        operation_id="projects_access_options_list",
    )
    def get(self, request, org, project):
        return super().get(request, org, project)
