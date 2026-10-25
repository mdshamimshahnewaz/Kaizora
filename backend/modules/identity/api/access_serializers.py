from rest_framework import serializers

from common.api import StrictSerializer


class PermissionsSerializer(serializers.Serializer):
    organization_id = serializers.UUIDField()
    membership_id = serializers.UUIDField()
    is_owner = serializers.BooleanField()
    permissions = serializers.ListField(child=serializers.CharField())


class RoleSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    scope_kind = serializers.ChoiceField(choices=["organization", "project"])
    status = serializers.ChoiceField(choices=["active", "archived"])
    version = serializers.IntegerField()
    permissions = serializers.ListField(child=serializers.CharField())


class CreateRoleSerializer(StrictSerializer):
    name = serializers.CharField(max_length=200)
    scope_kind = serializers.ChoiceField(
        choices=["organization", "project"], default="organization"
    )
    permissions = serializers.ListField(child=serializers.CharField(max_length=80), max_length=100)


class UpdateRoleSerializer(StrictSerializer):
    name = serializers.CharField(max_length=200, required=False)
    permissions = serializers.ListField(
        child=serializers.CharField(max_length=80), max_length=100, required=False
    )
    status = serializers.ChoiceField(choices=["active", "archived"], required=False)
    version = serializers.IntegerField(min_value=1)
    reason = serializers.CharField(max_length=500)


class RolePageSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    next = serializers.CharField(allow_null=True)
    previous = serializers.CharField(allow_null=True)
    results = RoleSerializer(many=True)


class AssignmentSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    membership_id = serializers.UUIDField()
    role_id = serializers.UUIDField()
    role_name = serializers.CharField()
    started_at = serializers.DateTimeField()
    ended_at = serializers.DateTimeField(allow_null=True)
    version = serializers.IntegerField()


class AssignmentPageSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    next = serializers.CharField(allow_null=True)
    previous = serializers.CharField(allow_null=True)
    results = AssignmentSerializer(many=True)


class AssignRoleSerializer(StrictSerializer):
    membership_id = serializers.UUIDField()
    role_id = serializers.UUIDField()
    reason = serializers.CharField(max_length=500)


class RevokeSerializer(StrictSerializer):
    version = serializers.IntegerField(min_value=1)
    reason = serializers.CharField(max_length=500)


class CatalogEntrySerializer(serializers.Serializer):
    key = serializers.CharField()
    scope = serializers.CharField()


class CatalogSerializer(serializers.Serializer):
    entries = CatalogEntrySerializer(many=True)
    presets = CreateRoleSerializer(many=True)
