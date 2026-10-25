from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from common.api import ERRORS, PAGE_PARAMS, page_parameters, page_response, validated
from modules.organizations.interfaces import resolve_scope

from .. import interfaces as service
from .serializers import (
    IdentityLinkCreateSerializer,
    IdentityLinkPageSerializer,
    IdentityLinkSerializer,
    LinkEndSerializer,
    MemberResourceCreateSerializer,
    ResourceCreateSerializer,
    ResourcePageSerializer,
    ResourceSerializer,
    ResourceUpdateSerializer,
    TeamCreateSerializer,
    TeamMembershipCreateSerializer,
    TeamMembershipEndSerializer,
    TeamMembershipPageSerializer,
    TeamMembershipSerializer,
    TeamPageSerializer,
    TeamSerializer,
    TeamUpdateSerializer,
    WorkerChoicePageSerializer,
    WorkerChoiceSerializer,
)


@method_decorator(never_cache, name="dispatch")
class ResourceListView(APIView):
    @extend_schema(
        parameters=[*PAGE_PARAMS, OpenApiParameter("search", str), OpenApiParameter("status", str)],
        responses={200: ResourcePageSerializer, **ERRORS},
        operation_id="resources_list",
    )
    def get(self, request, org):
        page, size = page_parameters(request, ("search", "status"))
        result = service.list_resources(
            resolve_scope(request.user.pk, org),
            page,
            size,
            request.query_params.get("search", ""),
            request.query_params.get("status"),
        )
        return page_response(request, page, size, result, ResourceSerializer)

    @extend_schema(request=ResourceCreateSerializer, responses={201: ResourceSerializer, **ERRORS})
    def post(self, request, org):
        return Response(
            ResourceSerializer(
                service.create_resource(
                    resolve_scope(request.user.pk, org),
                    **validated(ResourceCreateSerializer, request),
                )
            ).data,
            status=201,
        )


@method_decorator(never_cache, name="dispatch")
class ResourceView(APIView):
    @extend_schema(responses={200: ResourceSerializer, **ERRORS})
    def get(self, request, org, resource):
        return Response(
            ResourceSerializer(
                service.get_resource_summary(resolve_scope(request.user.pk, org), resource)
            ).data
        )

    @extend_schema(request=ResourceUpdateSerializer, responses={200: ResourceSerializer, **ERRORS})
    def patch(self, request, org, resource):
        return Response(
            ResourceSerializer(
                service.update_resource(
                    resolve_scope(request.user.pk, org),
                    resource,
                    **validated(ResourceUpdateSerializer, request),
                )
            ).data
        )


@method_decorator(never_cache, name="dispatch")
class TeamListView(APIView):
    @extend_schema(
        parameters=[*PAGE_PARAMS, OpenApiParameter("search", str), OpenApiParameter("status", str)],
        responses={200: TeamPageSerializer, **ERRORS},
        operation_id="teams_list",
    )
    def get(self, request, org):
        page, size = page_parameters(request, ("search", "status"))
        result = service.list_teams(
            resolve_scope(request.user.pk, org),
            page,
            size,
            request.query_params.get("search", ""),
            request.query_params.get("status"),
        )
        return page_response(request, page, size, result, TeamSerializer)

    @extend_schema(request=TeamCreateSerializer, responses={201: TeamSerializer, **ERRORS})
    def post(self, request, org):
        return Response(
            TeamSerializer(
                service.create_team(
                    resolve_scope(request.user.pk, org), **validated(TeamCreateSerializer, request)
                )
            ).data,
            status=201,
        )


@method_decorator(never_cache, name="dispatch")
class TeamView(APIView):
    @extend_schema(responses={200: TeamSerializer, **ERRORS})
    def get(self, request, org, team):
        return Response(
            TeamSerializer(service.get_team(resolve_scope(request.user.pk, org), team)).data
        )

    @extend_schema(request=TeamUpdateSerializer, responses={200: TeamSerializer, **ERRORS})
    def patch(self, request, org, team):
        return Response(
            TeamSerializer(
                service.update_team(
                    resolve_scope(request.user.pk, org),
                    team,
                    **validated(TeamUpdateSerializer, request),
                )
            ).data
        )


@method_decorator(never_cache, name="dispatch")
class IdentityLinksView(APIView):
    @extend_schema(
        parameters=PAGE_PARAMS,
        responses={200: IdentityLinkPageSerializer, **ERRORS},
        operation_id="resource_identity_links_list",
    )
    def get(self, request, org, resource):
        page, size = page_parameters(request)
        result = service.list_identity_links(
            resolve_scope(request.user.pk, org), resource, page, size
        )
        return page_response(request, page, size, result, IdentityLinkSerializer)

    @extend_schema(
        request=IdentityLinkCreateSerializer, responses={201: IdentityLinkSerializer, **ERRORS}
    )
    def post(self, request, org, resource):
        return Response(
            IdentityLinkSerializer(
                service.link_identity(
                    resolve_scope(request.user.pk, org),
                    resource,
                    **validated(IdentityLinkCreateSerializer, request),
                )
            ).data,
            status=201,
        )


@method_decorator(never_cache, name="dispatch")
class IdentityLinkEndView(APIView):
    @extend_schema(request=LinkEndSerializer, responses={200: IdentityLinkSerializer, **ERRORS})
    def post(self, request, org, resource, link):
        return Response(
            IdentityLinkSerializer(
                service.end_identity_link(
                    resolve_scope(request.user.pk, org),
                    resource,
                    link,
                    **validated(LinkEndSerializer, request),
                )
            ).data
        )


@method_decorator(never_cache, name="dispatch")
class TeamMembershipsView(APIView):
    @extend_schema(
        parameters=[*PAGE_PARAMS, OpenApiParameter("as_of", str)],
        responses={200: TeamMembershipPageSerializer, **ERRORS},
        operation_id="team_memberships_list",
    )
    def get(self, request, org, team):
        page, size = page_parameters(request, ("as_of",))
        as_of = (
            serializers.DateField().run_validation(request.query_params["as_of"])
            if "as_of" in request.query_params
            else None
        )
        result = service.get_team_members(
            resolve_scope(request.user.pk, org), team, as_of, page, size
        )
        return page_response(request, page, size, result, TeamMembershipSerializer)

    @extend_schema(
        request=TeamMembershipCreateSerializer, responses={201: TeamMembershipSerializer, **ERRORS}
    )
    def post(self, request, org, team):
        return Response(
            TeamMembershipSerializer(
                service.assign_team_member(
                    resolve_scope(request.user.pk, org),
                    team,
                    **validated(TeamMembershipCreateSerializer, request),
                )
            ).data,
            status=201,
        )


@method_decorator(never_cache, name="dispatch")
class TeamMembershipView(APIView):
    @extend_schema(
        request=TeamMembershipEndSerializer, responses={200: TeamMembershipSerializer, **ERRORS}
    )
    def patch(self, request, org, team, membership):
        return Response(
            TeamMembershipSerializer(
                service.end_team_membership(
                    resolve_scope(request.user.pk, org),
                    team,
                    membership,
                    **validated(TeamMembershipEndSerializer, request),
                )
            ).data
        )


@method_decorator(never_cache, name="dispatch")
class ResourceChoicesView(APIView):
    @extend_schema(
        parameters=[*PAGE_PARAMS, OpenApiParameter("kind", str), OpenApiParameter("search", str)],
        responses={200: WorkerChoicePageSerializer, **ERRORS},
    )
    def get(self, request, org):
        page, size = page_parameters(request, ("kind", "search"))
        result = service.resource_choices(
            resolve_scope(request.user.pk, org),
            request.query_params.get("kind", "members"),
            page,
            size,
            request.query_params.get("search", ""),
        )
        return page_response(request, page, size, result, WorkerChoiceSerializer)


@method_decorator(never_cache, name="dispatch")
class ResourceFromMemberView(APIView):
    @extend_schema(
        request=MemberResourceCreateSerializer, responses={200: ResourceSerializer, **ERRORS}
    )
    def post(self, request, org):
        return Response(
            ResourceSerializer(
                service.add_resource_from_member(
                    resolve_scope(request.user.pk, org),
                    **validated(MemberResourceCreateSerializer, request),
                )
            ).data
        )
