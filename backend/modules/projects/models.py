import uuid

from django.db import models
from django.db.models import Q


class Project(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization_id = models.UUIDField(db_index=True)
    code = models.CharField(max_length=32)
    normalized_code = models.CharField(max_length=32)
    name = models.CharField(max_length=200)
    type = models.CharField(
        max_length=10, choices=[("delivery", "Delivery"), ("operations", "Operations")]
    )
    status = models.CharField(
        max_length=10,
        default="draft",
        choices=[(s, s.title()) for s in ("draft", "active", "completed", "archived")],
    )
    client_id = models.UUIDField(null=True, blank=True)
    description = models.TextField(blank=True, max_length=4000)
    start_date = models.DateField(null=True, blank=True)
    target_end_date = models.DateField(null=True, blank=True)
    version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization_id", "normalized_code"], name="projects_unique_org_code"
            )
        ]
        indexes = [models.Index(fields=["organization_id", "status", "type", "id"])]

    def __str__(self):
        return f"{self.name} ({self.code})"


class ProjectAccess(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization_id = models.UUIDField(db_index=True)
    project = models.ForeignKey(Project, on_delete=models.PROTECT)
    membership_id = models.UUIDField()
    role_id = models.UUIDField()
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    version = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["project", "membership_id", "role_id"],
                condition=Q(ended_at__isnull=True),
                name="projects_unique_live_access",
            )
        ]
        indexes = [models.Index(fields=["project", "membership_id", "ended_at"])]


class ProjectChangeEvent(models.Model):
    organization_id = models.UUIDField(db_index=True)
    project = models.ForeignKey(Project, on_delete=models.PROTECT)
    access = models.ForeignKey(ProjectAccess, on_delete=models.PROTECT, null=True, blank=True)
    actor_id = models.UUIDField()
    action = models.CharField(max_length=30)
    reason = models.CharField(max_length=500)
    changed_fields = models.JSONField(default=list)
    before_version = models.PositiveIntegerField(default=0)
    after_version = models.PositiveIntegerField()
    occurred_at = models.DateTimeField(auto_now_add=True)


class ProjectWorker(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization_id = models.UUIDField(db_index=True)
    project = models.ForeignKey(Project, on_delete=models.PROTECT)
    resource_id = models.UUIDField()
    resource_name = models.CharField(max_length=200)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    version = models.PositiveIntegerField(default=1)
    added_by = models.UUIDField()
    ended_by = models.UUIDField(null=True, blank=True)
    reason = models.CharField(max_length=500)
    end_reason = models.CharField(max_length=500, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["project", "resource_id"],
                condition=Q(ended_at__isnull=True),
                name="projects_unique_live_worker",
            )
        ]
        indexes = [models.Index(fields=["project", "ended_at"])]
