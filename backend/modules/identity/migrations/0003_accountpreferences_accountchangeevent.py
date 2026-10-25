import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("identity", "0002_organizationrole_roleassignment_grantchangeevent_and_more")]
    operations = [
        migrations.CreateModel(
            name="AccountPreferences",
            fields=[
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        primary_key=True,
                        serialize=False,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "theme",
                    models.CharField(
                        blank=True,
                        choices=[("light", "Light"), ("dark", "Dark"), ("system", "System")],
                        max_length=10,
                        null=True,
                    ),
                ),
                ("timezone", models.CharField(blank=True, max_length=100, null=True)),
                ("version", models.PositiveIntegerField(default=1)),
            ],
        ),
        migrations.CreateModel(
            name="AccountChangeEvent",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("version", models.PositiveIntegerField()),
                ("changed_fields", models.JSONField(default=list)),
                ("occurred_at", models.DateTimeField(auto_now_add=True)),
                (
                    "actor",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="account_actions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="account_changes",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
