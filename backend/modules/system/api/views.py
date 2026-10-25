from dataclasses import asdict

from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.system.interfaces import liveness, readiness


class HealthSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["ok", "unavailable"])
    service = serializers.CharField()
    api_version = serializers.CharField()


class LivenessView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(responses={200: HealthSerializer}, auth=[])
    def get(self, request):
        return Response(asdict(liveness()))


class ReadinessView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(responses={200: HealthSerializer, 503: HealthSerializer}, auth=[])
    def get(self, request):
        result = readiness()
        return Response(asdict(result), status=200 if result.status == "ok" else 503)
