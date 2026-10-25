from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from common.api import ERRORS, PAGE_PARAMS, page_parameters, page_response, validated
from modules.organizations.interfaces import resolve_scope

from .. import interfaces as service
from .serializers import (
    ClientPageSerializer,
    ClientSerializer,
    ContactPageSerializer,
    ContactSerializer,
    CreateClientSerializer,
    CreateContactSerializer,
    UpdateClientSerializer,
    UpdateContactSerializer,
)


@method_decorator(never_cache, name="dispatch")
class ClientsView(APIView):
    @extend_schema(
        parameters=[
            *PAGE_PARAMS,
            OpenApiParameter("search", str),
            OpenApiParameter("status", str),
            OpenApiParameter("ordering", str),
        ],
        responses={200: ClientPageSerializer, **ERRORS},
        operation_id="clients_list",
    )
    def get(self, request, org):
        page, size = page_parameters(request, ("search", "status", "ordering"))
        result = service.list_clients(
            resolve_scope(request.user.pk, org),
            page,
            size,
            request.query_params.get("search", ""),
            request.query_params.get("status"),
            request.query_params.get("ordering", "name"),
        )
        return page_response(request, page, size, result, ClientSerializer)

    @extend_schema(request=CreateClientSerializer, responses={201: ClientSerializer, **ERRORS})
    def post(self, request, org):
        result = service.create_client(
            resolve_scope(request.user.pk, org), **validated(CreateClientSerializer, request)
        )
        return Response(ClientSerializer(result).data, status=201)


@method_decorator(never_cache, name="dispatch")
class ClientView(APIView):
    @extend_schema(responses={200: ClientSerializer, **ERRORS})
    def get(self, request, org, client):
        return Response(
            ClientSerializer(service.get_client(resolve_scope(request.user.pk, org), client)).data
        )

    @extend_schema(request=UpdateClientSerializer, responses={200: ClientSerializer, **ERRORS})
    def patch(self, request, org, client):
        result = service.update_client(
            resolve_scope(request.user.pk, org),
            client,
            **validated(UpdateClientSerializer, request),
        )
        return Response(ClientSerializer(result).data)


@method_decorator(never_cache, name="dispatch")
class ContactsView(APIView):
    @extend_schema(
        parameters=[*PAGE_PARAMS, OpenApiParameter("status", str)],
        responses={200: ContactPageSerializer, **ERRORS},
        operation_id="clients_contacts_list",
    )
    def get(self, request, org, client):
        page, size = page_parameters(request, ("status",))
        result = service.list_contacts(
            resolve_scope(request.user.pk, org),
            client,
            page,
            size,
            request.query_params.get("status"),
        )
        return page_response(request, page, size, result, ContactSerializer)

    @extend_schema(request=CreateContactSerializer, responses={201: ContactSerializer, **ERRORS})
    def post(self, request, org, client):
        result = service.create_contact(
            resolve_scope(request.user.pk, org),
            client,
            **validated(CreateContactSerializer, request),
        )
        return Response(ContactSerializer(result).data, status=201)


@method_decorator(never_cache, name="dispatch")
class ContactView(APIView):
    @extend_schema(responses={200: ContactSerializer, **ERRORS})
    def get(self, request, org, client, contact):
        result = service.get_contact(resolve_scope(request.user.pk, org), client, contact)
        return Response(ContactSerializer(result).data)

    @extend_schema(request=UpdateContactSerializer, responses={200: ContactSerializer, **ERRORS})
    def patch(self, request, org, client, contact):
        result = service.update_contact(
            resolve_scope(request.user.pk, org),
            client,
            contact,
            **validated(UpdateContactSerializer, request),
        )
        return Response(ContactSerializer(result).data)
