from rest_framework import serializers

from common.api import StrictSerializer


class ClientSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    code = serializers.CharField()
    name = serializers.CharField()
    status = serializers.ChoiceField(choices=["active", "archived"])
    version = serializers.IntegerField()
    created_at = serializers.DateTimeField()


class ClientPageSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    next = serializers.CharField(allow_null=True)
    previous = serializers.CharField(allow_null=True)
    results = ClientSerializer(many=True)


class CreateClientSerializer(StrictSerializer):
    code = serializers.CharField(max_length=32)
    name = serializers.CharField(max_length=200)


class UpdateClientSerializer(StrictSerializer):
    name = serializers.CharField(max_length=200, required=False)
    status = serializers.ChoiceField(choices=["active", "archived"], required=False)
    version = serializers.IntegerField(min_value=1)
    reason = serializers.CharField(max_length=500)


class ContactSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    client_id = serializers.UUIDField()
    name = serializers.CharField()
    email = serializers.EmailField(allow_blank=True)
    phone = serializers.CharField(allow_blank=True)
    position = serializers.CharField(allow_blank=True)
    status = serializers.ChoiceField(choices=["active", "retired"])
    version = serializers.IntegerField()


class ContactPageSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    next = serializers.CharField(allow_null=True)
    previous = serializers.CharField(allow_null=True)
    results = ContactSerializer(many=True)


class CreateContactSerializer(StrictSerializer):
    name = serializers.CharField(max_length=200)
    email = serializers.EmailField(max_length=254, allow_blank=True, required=False)
    phone = serializers.CharField(max_length=50, allow_blank=True, required=False)
    position = serializers.CharField(max_length=200, allow_blank=True, required=False)


class UpdateContactSerializer(StrictSerializer):
    name = serializers.CharField(max_length=200, required=False)
    email = serializers.EmailField(max_length=254, allow_blank=True, required=False)
    phone = serializers.CharField(max_length=50, allow_blank=True, required=False)
    position = serializers.CharField(max_length=200, allow_blank=True, required=False)
    status = serializers.ChoiceField(choices=["active", "retired"], required=False)
    version = serializers.IntegerField(min_value=1)
    reason = serializers.CharField(max_length=500)
