from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from common.api import (
    ERRORS,
    PAGE_PARAMS,
    StrictSerializer,
    page_parameters,
    page_response,
    validated,
)
from modules.organizations.interfaces import resolve_scope

from .. import interfaces as service
from .serializers import ProjectOptionPageSerializer, ProjectOptionSerializer


class ProjectWorkerSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    resource_id = serializers.UUIDField()
    resource_name = serializers.CharField()
    started_at = serializers.DateTimeField()
    ended_at = serializers.DateTimeField(allow_null=True)
    version = serializers.IntegerField()


class ProjectWorkerPageSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    next = serializers.CharField(allow_null=True)
    previous = serializers.CharField(allow_null=True)
    results = ProjectWorkerSerializer(many=True)


class AddProjectWorkerSerializer(StrictSerializer):
    resource_id = serializers.UUIDField(required=False)
    membership_id = serializers.UUIDField(required=False)
    reason = serializers.CharField(max_length=500)


class EndProjectWorkerSerializer(StrictSerializer):
    version = serializers.IntegerField(min_value=1)
    reason = serializers.CharField(max_length=500)


@method_decorator(never_cache, name="dispatch")
class WorkforceView(APIView):
    @extend_schema(parameters=PAGE_PARAMS, responses={200: ProjectWorkerPageSerializer, **ERRORS})
    def get(self, request, org, project):
        page, size = page_parameters(request)
        result = service.list_workers(resolve_scope(request.user.pk, org), project, page, size)
        return page_response(request, page, size, result, ProjectWorkerSerializer)

    @extend_schema(
        request=AddProjectWorkerSerializer, responses={201: ProjectWorkerSerializer, **ERRORS}
    )
    def post(self, request, org, project):
        return Response(
            ProjectWorkerSerializer(
                service.add_worker(
                    resolve_scope(request.user.pk, org),
                    project,
                    **validated(AddProjectWorkerSerializer, request),
                )
            ).data,
            status=201,
        )


@method_decorator(never_cache, name="dispatch")
class WorkforceEndView(APIView):
    @extend_schema(
        request=EndProjectWorkerSerializer, responses={200: ProjectWorkerSerializer, **ERRORS}
    )
    def post(self, request, org, project, worker):
        return Response(
            ProjectWorkerSerializer(
                service.end_worker(
                    resolve_scope(request.user.pk, org),
                    project,
                    worker,
                    **validated(EndProjectWorkerSerializer, request),
                )
            ).data
        )


@method_decorator(never_cache, name="dispatch")
class WorkforceOptionsView(APIView):
    @extend_schema(
        parameters=[*PAGE_PARAMS, OpenApiParameter("kind", str), OpenApiParameter("search", str)],
        responses={200: ProjectOptionPageSerializer, **ERRORS},
    )
    def get(self, request, org, project):
        page, size = page_parameters(request, ("kind", "search"))
        result = service.worker_options(
            resolve_scope(request.user.pk, org),
            project,
            request.query_params.get("kind", "members"),
            page,
            size,
            request.query_params.get("search", ""),
        )
        return page_response(request, page, size, result, ProjectOptionSerializer)
