from rest_framework import serializers


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, trim_whitespace=False, max_length=4096)


class UserSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    username = serializers.CharField()
    display_name = serializers.CharField()
    email = serializers.EmailField(allow_blank=True)


class SessionSerializer(serializers.Serializer):
    user = UserSerializer(allow_null=True)
    csrf_token = serializers.CharField()


class AuthErrorSerializer(serializers.Serializer):
    detail = serializers.CharField()
