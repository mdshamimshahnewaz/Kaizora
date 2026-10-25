from rest_framework import serializers

from common.api import StrictSerializer


class ResourceSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    code = serializers.CharField()
    display_name = serializers.CharField()
    status = serializers.ChoiceField(choices=["active", "retired"])
    version = serializers.IntegerField()
    linked_membership_id = serializers.UUIDField(allow_null=True)


class ResourcePageSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    next = serializers.CharField(allow_null=True)
    previous = serializers.CharField(allow_null=True)
    results = ResourceSerializer(many=True)


class TeamSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    code = serializers.CharField()
    name = serializers.CharField()
    status = serializers.ChoiceField(choices=["active", "archived"])
    version = serializers.IntegerField()


class TeamPageSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    next = serializers.CharField(allow_null=True)
    previous = serializers.CharField(allow_null=True)
    results = TeamSerializer(many=True)


class IdentityLinkSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    resource_id = serializers.UUIDField()
    membership_id = serializers.UUIDField()
    started_at = serializers.DateTimeField()
    ended_at = serializers.DateTimeField(allow_null=True)
    reason = serializers.CharField()
    resource_version = serializers.IntegerField()


class IdentityLinkPageSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    next = serializers.CharField(allow_null=True)
    previous = serializers.CharField(allow_null=True)
    results = IdentityLinkSerializer(many=True)


class TeamMembershipSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    team_id = serializers.UUIDField()
    resource_id = serializers.UUIDField()
    resource_name = serializers.CharField()
    resource_status = serializers.CharField()
    start_date = serializers.DateField()
    end_date = serializers.DateField(allow_null=True)
    version = serializers.IntegerField()


class TeamMembershipPageSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    next = serializers.CharField(allow_null=True)
    previous = serializers.CharField(allow_null=True)
    results = TeamMembershipSerializer(many=True)


class ResourceCreateSerializer(StrictSerializer):
    code = serializers.CharField(max_length=32, required=False, allow_blank=True)
    display_name = serializers.CharField(max_length=200)


class TeamCreateSerializer(StrictSerializer):
    code = serializers.CharField(max_length=32)
    name = serializers.CharField(max_length=200)


class ResourceUpdateSerializer(StrictSerializer):
    display_name = serializers.CharField(max_length=200, required=False)
    status = serializers.ChoiceField(choices=["active", "retired"], required=False)
    version = serializers.IntegerField(min_value=1)
    reason = serializers.CharField(max_length=500)


class TeamUpdateSerializer(StrictSerializer):
    name = serializers.CharField(max_length=200, required=False)
    status = serializers.ChoiceField(choices=["active", "archived"], required=False)
    version = serializers.IntegerField(min_value=1)
    reason = serializers.CharField(max_length=500)


class LinkEndSerializer(StrictSerializer):
    version = serializers.IntegerField(min_value=1)
    reason = serializers.CharField(max_length=500)


class IdentityLinkCreateSerializer(LinkEndSerializer):
    membership_id = serializers.UUIDField()


class TeamMembershipCreateSerializer(StrictSerializer):
    resource_id = serializers.UUIDField(required=False)
    membership_id = serializers.UUIDField(required=False)
    start_date = serializers.DateField()
    end_date = serializers.DateField(allow_null=True, required=False)


class TeamMembershipEndSerializer(LinkEndSerializer):
    end_date = serializers.DateField()


class MemberResourceCreateSerializer(StrictSerializer):
    membership_id = serializers.UUIDField()


class WorkerChoiceSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    label = serializers.CharField()


class WorkerChoicePageSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    next = serializers.CharField(allow_null=True)
    previous = serializers.CharField(allow_null=True)
    results = WorkerChoiceSerializer(many=True)
