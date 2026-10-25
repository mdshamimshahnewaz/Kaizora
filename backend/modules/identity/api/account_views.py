from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from common.api import ERRORS, validated

from ..account import get_account, update_account
from .account_serializers import AccountQuerySerializer, AccountSerializer, UpdateAccountSerializer


@method_decorator(never_cache, name="dispatch")
class AccountView(APIView):
    @extend_schema(
        parameters=[AccountQuerySerializer], responses={200: AccountSerializer, **ERRORS}
    )
    def get(self, request):
        if any(len(request.query_params.getlist(key)) != 1 for key in request.query_params):
            raise ValidationError({"detail": "Duplicate query parameters are not supported."})
        query = AccountQuerySerializer(data=request.query_params.dict())
        query.is_valid(raise_exception=True)
        return Response(
            AccountSerializer(get_account(request.user.pk, **query.validated_data)).data
        )

    @extend_schema(request=UpdateAccountSerializer, responses={200: AccountSerializer, **ERRORS})
    def patch(self, request):
        return Response(
            AccountSerializer(
                update_account(request.user.pk, **validated(UpdateAccountSerializer, request))
            ).data
        )
