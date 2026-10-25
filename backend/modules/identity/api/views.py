from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.csrf import csrf_failure as default_csrf_failure
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import SimpleRateThrottle
from rest_framework.views import APIView

from .serializers import AuthErrorSerializer, LoginSerializer, SessionSerializer


def csrf_failure(request, reason=""):
    if request.path.startswith("/api/v1/auth/"):
        return JsonResponse(
            {"detail": "CSRF verification failed. Refresh and try again."}, status=403
        )
    return default_csrf_failure(request, reason=reason)


def session_payload(request):
    user = request.user
    return {
        "user": {
            "id": str(user.pk),
            "username": user.username,
            "display_name": user.get_full_name() or user.username,
            "email": user.email,
        }
        if user.is_authenticated and user.is_active
        else None,
        "csrf_token": get_token(request),
    }


class LoginThrottle(SimpleRateThrottle):
    scope = "login"
    rate = "10/minute"

    def get_cache_key(self, request, view):
        return self.cache_format % {"scope": self.scope, "ident": self.get_ident(request)}


@method_decorator(never_cache, name="dispatch")
class SessionView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(responses=SessionSerializer)
    def get(self, request):
        return Response(session_payload(request))


@method_decorator(never_cache, name="dispatch")
@method_decorator(csrf_protect, name="dispatch")
class LoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [LoginThrottle]

    @extend_schema(
        request=LoginSerializer,
        responses={
            200: SessionSerializer,
            400: AuthErrorSerializer,
            403: AuthErrorSerializer,
            429: AuthErrorSerializer,
        },
        auth=[],
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"detail": "Enter a valid username and password."}, status=400)
        user = authenticate(request=request._request, **serializer.validated_data)
        if user is None:
            return Response({"detail": "Invalid username or password."}, status=400)
        login(request._request, user)
        # DRF's request.user was anonymous before login; serialize Django's new user.
        return Response(session_payload(request._request))


@method_decorator(never_cache, name="dispatch")
@method_decorator(csrf_protect, name="dispatch")
class LogoutView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(request=None, responses={204: None, 403: AuthErrorSerializer}, auth=[])
    def post(self, request):
        logout(request._request)
        return Response(status=204)
