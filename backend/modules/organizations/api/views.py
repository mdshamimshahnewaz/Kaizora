from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from common.api import ERRORS, PAGE_PARAMS, page_parameters, page_response, validated

from .. import interfaces as service
from .serializers import (
    AddMembershipSerializer,
    ChangeMembershipSerializer,
    CreateOrganizationSerializer,
    MembershipPageSerializer,
    MembershipSerializer,
    OrganizationPageSerializer,
    OrganizationSerializer,
    ProvisioningSerializer,
    TransferOwnerSerializer,
)


@method_decorator(never_cache, name="dispatch")
class OrganizationsView(APIView):
    @extend_schema(
        operation_id="organizations_list",
        parameters=PAGE_PARAMS,
        responses={200: OrganizationPageSerializer, **ERRORS},
    )
    def get(self, request):
        page, size = page_parameters(request)
        result = service.list_my_organizations(request.user.pk, page, size)
        return page_response(request, page, size, result, OrganizationSerializer)

    @extend_schema(
        request=CreateOrganizationSerializer, responses={201: OrganizationSerializer, **ERRORS}
    )
    def post(self, request):
        result = service.create_organization(
            request.user.pk, **validated(CreateOrganizationSerializer, request)
        )
        return Response(OrganizationSerializer(result).data, status=201)


@method_decorator(never_cache, name="dispatch")
class OrganizationView(APIView):
    @extend_schema(responses={200: OrganizationSerializer, **ERRORS})
    def get(self, request, org):
        return Response(OrganizationSerializer(service.get_organization(request.user.pk, org)).data)


@method_decorator(never_cache, name="dispatch")
class MembershipsView(APIView):
    @extend_schema(
        parameters=[*PAGE_PARAMS, OpenApiParameter("status", str)],
        responses={200: MembershipPageSerializer, **ERRORS},
    )
    def get(self, request, org):
        page, size = page_parameters(request, ("status",))
        result = service.list_memberships(
            request.user.pk, org, page, size, request.query_params.get("status")
        )
        return page_response(request, page, size, result, MembershipSerializer)

    @extend_schema(request=AddMembershipSerializer, responses={201: MembershipSerializer, **ERRORS})
    def post(self, request, org):
        result = service.add_membership(
            request.user.pk, org, **validated(AddMembershipSerializer, request)
        )
        return Response(MembershipSerializer(result).data, status=201)


class MembershipView(APIView):
    @extend_schema(
        request=ChangeMembershipSerializer, responses={200: MembershipSerializer, **ERRORS}
    )
    def patch(self, request, org, member):
        result = service.change_membership(
            request.user.pk, org, member, **validated(ChangeMembershipSerializer, request)
        )
        return Response(MembershipSerializer(result).data)


class TransferOwnerView(APIView):
    @extend_schema(
        request=TransferOwnerSerializer, responses={200: OrganizationSerializer, **ERRORS}
    )
    def post(self, request, org):
        result = service.transfer_owner(
            request.user.pk, org, **validated(TransferOwnerSerializer, request)
        )
        return Response(OrganizationSerializer(result).data)


@method_decorator(never_cache, name="dispatch")
class ProvisioningView(APIView):
    @extend_schema(responses={200: ProvisioningSerializer, **ERRORS})
    def get(self, request):
        return Response({"can_create": service.provisioning_capability(request.user.pk)})
