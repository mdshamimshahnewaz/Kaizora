from rest_framework import serializers

from common.api import StrictSerializer


class PreferencesSerializer(StrictSerializer):
    theme = serializers.ChoiceField(
        choices=["light", "dark", "system"], allow_null=True, required=False
    )
    timezone = serializers.CharField(max_length=100, allow_null=True, required=False)


class AccountSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    username = serializers.CharField()
    email = serializers.EmailField(allow_blank=True)
    first_name = serializers.CharField(allow_blank=True)
    last_name = serializers.CharField(allow_blank=True)
    display_name = serializers.CharField()
    preferences = PreferencesSerializer()
    version = serializers.IntegerField()
    effective_timezone = serializers.CharField()


class UpdateAccountSerializer(StrictSerializer):
    version = serializers.IntegerField(min_value=1)
    first_name = serializers.CharField(max_length=150, allow_blank=True, required=False)
    last_name = serializers.CharField(max_length=150, allow_blank=True, required=False)
    preferences = PreferencesSerializer(required=False)


class AccountQuerySerializer(StrictSerializer):
    organization = serializers.UUIDField(required=False)
