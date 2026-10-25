from rest_framework import serializers

from common.api import StrictSerializer


class ProjectSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    code = serializers.CharField()
    name = serializers.CharField()
    type = serializers.ChoiceField(choices=["delivery", "operations"])
    status = serializers.ChoiceField(choices=["draft", "active", "completed", "archived"])
    client_id = serializers.UUIDField(allow_null=True)
    client_name = serializers.CharField(allow_blank=True)
    description = serializers.CharField(allow_blank=True)
    start_date = serializers.DateField(allow_null=True)
    target_end_date = serializers.DateField(allow_null=True)
    version = serializers.IntegerField()
    created_at = serializers.DateTimeField()
    capabilities = serializers.ListField(child=serializers.CharField())


class ProjectPageSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    next = serializers.CharField(allow_null=True)
    previous = serializers.CharField(allow_null=True)
    results = ProjectSerializer(many=True)


class CreateProjectSerializer(StrictSerializer):
    code = serializers.CharField(max_length=32)
    name = serializers.CharField(max_length=200)
    type = serializers.ChoiceField(choices=["delivery", "operations"])
    client_id = serializers.UUIDField(allow_null=True, required=False)
    description = serializers.CharField(max_length=4000, allow_blank=True, required=False)
    start_date = serializers.DateField(allow_null=True, required=False)
    target_end_date = serializers.DateField(allow_null=True, required=False)
    initial_manager_membership_id = serializers.UUIDField()
    initial_manager_role_id = serializers.UUIDField()


class UpdateProjectSerializer(StrictSerializer):
    name = serializers.CharField(max_length=200, required=False)
    description = serializers.CharField(max_length=4000, allow_blank=True, required=False)
    start_date = serializers.DateField(allow_null=True, required=False)
    target_end_date = serializers.DateField(allow_null=True, required=False)
    version = serializers.IntegerField(min_value=1)
    reason = serializers.CharField(max_length=500)


class TransitionProjectSerializer(StrictSerializer):
    target_status = serializers.ChoiceField(choices=["draft", "active", "completed", "archived"])
    version = serializers.IntegerField(min_value=1)
    reason = serializers.CharField(max_length=500)


class ProjectAccessSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    membership_id = serializers.UUIDField()
    member_name = serializers.CharField()
    role_id = serializers.UUIDField()
    role_name = serializers.CharField()
    started_at = serializers.DateTimeField()
    ended_at = serializers.DateTimeField(allow_null=True)
    version = serializers.IntegerField()


class ProjectAccessPageSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    next = serializers.CharField(allow_null=True)
    previous = serializers.CharField(allow_null=True)
    results = ProjectAccessSerializer(many=True)


class GrantProjectAccessSerializer(StrictSerializer):
    membership_id = serializers.UUIDField()
    role_id = serializers.UUIDField()
    reason = serializers.CharField(max_length=500)


class EndProjectAccessSerializer(StrictSerializer):
    version = serializers.IntegerField(min_value=1)
    reason = serializers.CharField(max_length=500)


class ProjectOptionSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    label = serializers.CharField()


class ProjectOptionPageSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    next = serializers.CharField(allow_null=True)
    previous = serializers.CharField(allow_null=True)
    results = ProjectOptionSerializer(many=True)
