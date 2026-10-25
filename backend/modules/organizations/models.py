import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q


class Organization(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    timezone = models.CharField(max_length=64, default="Asia/Dhaka")
    status = models.CharField(max_length=16, default="active", choices=[("active", "Active")])
    version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        permissions = [("bootstrap_organization", "Can provision an organization and first owner")]
        constraints = [
            models.CheckConstraint(condition=Q(status="active"), name="org_active_status")
        ]

    def __str__(self):
        return self.name


class Membership(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        SUSPENDED = "suspended", "Suspended"
        ENDED = "ended", "Ended"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)
    is_owner = models.BooleanField(default=False)
    version = models.PositiveIntegerField(default=1)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["organization", "user"], name="org_unique_member"),
            models.CheckConstraint(
                condition=Q(status__in=["active", "suspended", "ended"]), name="org_member_status"
            ),
        ]
        indexes = [
            models.Index(fields=["user", "status"], name="org_member_user_status"),
            models.Index(fields=["organization", "status", "id"], name="org_member_org_status"),
        ]


class MembershipStatusEvent(models.Model):
    membership = models.ForeignKey(Membership, on_delete=models.PROTECT)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    occurred_at = models.DateTimeField(auto_now_add=True)
    reason = models.CharField(max_length=500)
    before_status = models.CharField(max_length=16, blank=True)
    after_status = models.CharField(max_length=16)
    before_owner = models.BooleanField(default=False)
    after_owner = models.BooleanField(default=False)


class OrganizationChangeEvent(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    occurred_at = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=40)
    reason = models.CharField(max_length=500)
    before_version = models.PositiveIntegerField(default=0)
    after_version = models.PositiveIntegerField()
