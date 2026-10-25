import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)


class OrganizationRole(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey("organizations.Organization", on_delete=models.PROTECT)
    name = models.CharField(max_length=200)
    scope_kind = models.CharField(
        max_length=20,
        choices=[("organization", "Organization"), ("project", "Project")],
        default="organization",
    )
    status = models.CharField(
        max_length=20, choices=[("active", "Active"), ("archived", "Archived")], default="active"
    )
    version = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                models.functions.Lower("name"), "organization", name="identity_role_name_unique"
            ),
            models.CheckConstraint(
                condition=models.Q(scope_kind__in=["organization", "project"]),
                name="identity_role_scope_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(status__in=["active", "archived"]),
                name="identity_role_status_valid",
            ),
        ]
        indexes = [models.Index(fields=["organization", "name", "id"])]


class RolePermission(models.Model):
    role = models.ForeignKey(
        OrganizationRole, on_delete=models.PROTECT, related_name="permission_records"
    )
    key = models.CharField(max_length=80)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["role", "key"], name="identity_role_key_unique")
        ]


class RoleAssignment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey("organizations.Organization", on_delete=models.PROTECT)
    membership = models.ForeignKey("organizations.Membership", on_delete=models.PROTECT)
    role = models.ForeignKey(OrganizationRole, on_delete=models.PROTECT)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    version = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["membership", "role"],
                condition=models.Q(ended_at__isnull=True),
                name="identity_live_assignment_unique",
            )
        ]
        indexes = [models.Index(fields=["organization", "membership", "ended_at"])]


class GrantChangeEvent(models.Model):
    id = models.BigAutoField(primary_key=True)
    organization = models.ForeignKey("organizations.Organization", on_delete=models.PROTECT)
    actor = models.ForeignKey(User, on_delete=models.PROTECT)
    role = models.ForeignKey(OrganizationRole, on_delete=models.PROTECT)
    assignment = models.ForeignKey(RoleAssignment, on_delete=models.PROTECT, null=True)
    action = models.CharField(max_length=30)
    reason = models.CharField(max_length=500)
    occurred_at = models.DateTimeField(auto_now_add=True)
    before = models.JSONField(default=dict)
    after = models.JSONField(default=dict)


class AccountPreferences(models.Model):
    user = models.OneToOneField(User, on_delete=models.PROTECT, primary_key=True)
    theme = models.CharField(
        max_length=10,
        choices=[("light", "Light"), ("dark", "Dark"), ("system", "System")],
        null=True,
        blank=True,
    )
    timezone = models.CharField(max_length=100, null=True, blank=True)
    version = models.PositiveIntegerField(default=1)

    def __str__(self):
        return str(self.user)


class AccountChangeEvent(models.Model):
    actor = models.ForeignKey(User, on_delete=models.PROTECT, related_name="account_actions")
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="account_changes")
    version = models.PositiveIntegerField()
    changed_fields = models.JSONField(default=list)
    occurred_at = models.DateTimeField(auto_now_add=True)
