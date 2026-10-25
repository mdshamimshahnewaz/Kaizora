import uuid

from django.db import models


class Client(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        ARCHIVED = "archived", "Archived"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization_id = models.UUIDField(db_index=True)
    code = models.CharField(max_length=32)
    normalized_code = models.CharField(max_length=32)
    name = models.CharField(max_length=200)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization_id", "normalized_code"], name="clients_unique_org_code"
            )
        ]
        indexes = [models.Index(fields=["organization_id", "status", "name", "id"])]

    def __str__(self):
        return f"{self.name} ({self.code})"


class Contact(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        RETIRED = "retired", "Retired"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization_id = models.UUIDField(db_index=True)
    client = models.ForeignKey(Client, on_delete=models.PROTECT, related_name="contacts")
    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    position = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    version = models.PositiveIntegerField(default=1)

    class Meta:
        indexes = [models.Index(fields=["organization_id", "client", "status", "name", "id"])]

    def __str__(self):
        return self.name


class ChangeEvent(models.Model):
    organization_id = models.UUIDField(db_index=True)
    actor_id = models.UUIDField()
    action = models.CharField(max_length=30)
    reason = models.CharField(max_length=500)
    changed_fields = models.JSONField(default=list)
    before_version = models.PositiveIntegerField(default=0)
    after_version = models.PositiveIntegerField()
    occurred_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class ClientChangeEvent(ChangeEvent):
    client = models.ForeignKey(Client, on_delete=models.PROTECT)


class ContactChangeEvent(ChangeEvent):
    contact = models.ForeignKey(Contact, on_delete=models.PROTECT)
