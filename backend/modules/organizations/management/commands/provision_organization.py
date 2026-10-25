from django.core.management.base import BaseCommand, CommandError
from rest_framework.exceptions import APIException

from modules.organizations.interfaces import create_organization, get_active_identity


class Command(BaseCommand):
    help = "Provision an organization for an existing user, using an authorized operator."

    def add_arguments(self, parser):
        actor = parser.add_mutually_exclusive_group(required=True)
        actor.add_argument("--actor-id", type=str)
        actor.add_argument("--actor-username", type=str)
        owner = parser.add_mutually_exclusive_group(required=True)
        owner.add_argument("--owner-id", type=str)
        owner.add_argument("--owner-username", type=str)
        parser.add_argument("--name", required=True)
        parser.add_argument("--timezone", default="Asia/Dhaka")

    def handle(self, *args, **options):
        from uuid import UUID

        def identity_id(kind):
            if options[f"{kind}_id"]:
                return UUID(options[f"{kind}_id"])
            identity = get_active_identity(username=options[f"{kind}_username"])
            if identity is None:
                raise CommandError(f"Choose an active existing {kind} account.")
            return identity.id

        try:
            org = create_organization(
                identity_id("actor"),
                options["name"],
                options["timezone"],
                identity_id("owner"),
            )
        except (APIException, ValueError) as error:
            raise CommandError(str(error)) from error
        self.stdout.write(self.style.SUCCESS(f"Created organization {org.id}"))
