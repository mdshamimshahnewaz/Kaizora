from rest_framework import serializers

from common.api import StrictSerializer


class OrganizationSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    timezone = serializers.CharField()
    status = serializers.CharField()
    version = serializers.IntegerField()
    membership_id = serializers.UUIDField(allow_null=True)
    is_owner = serializers.BooleanField()


class OrganizationPageSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    next = serializers.CharField(allow_null=True)
    previous = serializers.CharField(allow_null=True)
    results = OrganizationSerializer(many=True)


class CreateOrganizationSerializer(StrictSerializer):
    name = serializers.CharField(max_length=200)
    timezone = serializers.CharField(max_length=64)
    owner_user_id = serializers.UUIDField(required=False)
    owner_username = serializers.CharField(max_length=150, required=False)


class MembershipSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    user_id = serializers.UUIDField()
    status = serializers.ChoiceField(choices=["active", "suspended", "ended"])
    is_owner = serializers.BooleanField()
    version = serializers.IntegerField()
    joined_at = serializers.DateTimeField()
    username = serializers.CharField()
    display_name = serializers.CharField()


class MembershipPageSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    next = serializers.CharField(allow_null=True)
    previous = serializers.CharField(allow_null=True)
    results = MembershipSerializer(many=True)


class AddMembershipSerializer(StrictSerializer):
    user_id = serializers.UUIDField(required=False)
    username = serializers.CharField(max_length=150, required=False)


class ChangeMembershipSerializer(StrictSerializer):
    status = serializers.ChoiceField(choices=["active", "suspended", "ended"])
    version = serializers.IntegerField(min_value=1)
    reason = serializers.CharField(max_length=500)


class TransferOwnerSerializer(StrictSerializer):
    target_membership_id = serializers.UUIDField()
    version = serializers.IntegerField(min_value=1)
    reason = serializers.CharField(max_length=500)


class ProvisioningSerializer(serializers.Serializer):
    can_create = serializers.BooleanField()
