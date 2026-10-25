import uuid

from django.db import models


class NamedRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization_id = models.UUIDField(db_index=True)
    code = models.CharField(max_length=32)
    normalized_code = models.CharField(max_length=32)
    version = models.PositiveIntegerField(default=1)

    class Meta:
        abstract = True


class Resource(NamedRecord):
    display_name = models.CharField(max_length=200)
    status = models.CharField(
        max_length=10, choices=[("active", "Active"), ("retired", "Retired")], default="active"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization_id", "normalized_code"], name="resources_unique_code"
            )
        ]
        indexes = [models.Index(fields=["organization_id", "status", "display_name", "id"])]

    def __str__(self):
        return f"{self.display_name} ({self.code})"


class Team(NamedRecord):
    name = models.CharField(max_length=200)
    status = models.CharField(
        max_length=10, choices=[("active", "Active"), ("archived", "Archived")], default="active"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization_id", "normalized_code"], name="teams_unique_code"
            )
        ]
        indexes = [models.Index(fields=["organization_id", "status", "name", "id"])]

    def __str__(self):
        return f"{self.name} ({self.code})"


class ResourceIdentityLink(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization_id = models.UUIDField(db_index=True)
    resource = models.ForeignKey(Resource, on_delete=models.PROTECT)
    membership_id = models.UUIDField()
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True)
    reason = models.CharField(max_length=500)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["resource"],
                condition=models.Q(ended_at__isnull=True),
                name="resource_live_identity",
            ),
            models.UniqueConstraint(
                fields=["organization_id", "membership_id"],
                condition=models.Q(ended_at__isnull=True),
                name="membership_live_resource",
            ),
        ]

    def __str__(self):
        return f"{self.resource} — linked {self.started_at:%Y-%m-%d}"


class TeamMembership(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization_id = models.UUIDField(db_index=True)
    team = models.ForeignKey(Team, on_delete=models.PROTECT)
    resource = models.ForeignKey(Resource, on_delete=models.PROTECT)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    version = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(end_date__isnull=True)
                | models.Q(end_date__gt=models.F("start_date")),
                name="team_interval_valid",
            )
        ]
        indexes = [models.Index(fields=["organization_id", "team", "resource", "start_date"])]

    def __str__(self):
        return f"{self.resource} / {self.team} / {self.start_date}"


class ResourceChangeEvent(models.Model):
    organization_id = models.UUIDField(db_index=True)
    actor_id = models.UUIDField()
    entity_id = models.UUIDField()
    entity_type = models.CharField(max_length=30)
    action = models.CharField(max_length=30)
    reason = models.CharField(max_length=500)
    details = models.JSONField(default=dict)
    occurred_at = models.DateTimeField(auto_now_add=True)
