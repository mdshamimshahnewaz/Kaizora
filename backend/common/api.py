from dataclasses import dataclass
from urllib.parse import urlencode

from drf_spectacular.utils import OpenApiParameter
from rest_framework import serializers
from rest_framework.exceptions import APIException, NotFound, ValidationError
from rest_framework.response import Response


class Conflict(APIException):
    status_code = 409
    default_detail = "This record changed. Refresh and try again."


class StrictSerializer(serializers.Serializer):
    def to_internal_value(self, data):
        if isinstance(data, dict):
            unknown = set(data) - set(self.fields)
            if unknown:
                raise serializers.ValidationError(
                    {key: "Unknown field." for key in sorted(unknown)}
                )
        return super().to_internal_value(data)


class ErrorSerializer(serializers.Serializer):
    detail = serializers.CharField()


@dataclass(frozen=True)
class PageDTO:
    count: int
    results: tuple


def paginate(query, page, size, convert):
    if not isinstance(page, int) or page < 1 or not isinstance(size, int) or not 1 <= size <= 100:
        raise ValidationError({"page": "Use a positive page and page_size between 1 and 100."})
    count = query.count()
    if page > 1 and (page - 1) * size >= count:
        raise NotFound("Page not found.")
    return PageDTO(count, tuple(convert(item) for item in query[(page - 1) * size : page * size]))


def reason_text(reason):
    if not isinstance(reason, str) or not reason.strip() or len(reason) > 500:
        raise ValidationError({"reason": "Provide a reason of 1–500 characters."})
    return reason.strip()


PAGE_PARAMS = [OpenApiParameter("page", int), OpenApiParameter("page_size", int)]
ERRORS = {400: ErrorSerializer, 403: ErrorSerializer, 404: ErrorSerializer, 409: ErrorSerializer}


def validated(serializer_class, request):
    serializer = serializer_class(data=request.data)
    serializer.is_valid(raise_exception=True)
    return serializer.validated_data


def page_parameters(request, extra=()):
    if set(request.query_params) - {"page", "page_size", *extra}:
        raise ValidationError({"detail": "Unknown query parameter."})
    if any(len(request.query_params.getlist(key)) != 1 for key in request.query_params):
        raise ValidationError({"detail": "Duplicate query parameters are not supported."})
    try:
        page = int(request.query_params.get("page", "1"))
        size = int(request.query_params.get("page_size", "50"))
    except ValueError:
        raise ValidationError({"detail": "Invalid pagination."}) from None
    return page, size


def page_response(request, page, size, result, serializer_class):
    def link(number):
        params = request.query_params.dict()
        params.update(page=number, page_size=size)
        return f"{request.path}?{urlencode(params)}"

    return Response(
        {
            "count": result.count,
            "next": link(page + 1) if page * size < result.count else None,
            "previous": link(page - 1) if page > 1 else None,
            "results": serializer_class(result.results, many=True).data,
        }
    )
