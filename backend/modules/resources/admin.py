from django import forms
from django.contrib import admin
from rest_framework.exceptions import PermissionDenied

from common.admin import CommandAdmin, ReadOnlyAdmin
from common.widgets import SearchableSelect
from modules.organizations.interfaces import (
    authorized_organization_ids,
    get_organization,
    list_memberships,
    resolve_scope,
)

from . import interfaces as service
from .models import Resource, ResourceChangeEvent, ResourceIdentityLink, Team, TeamMembership


class ScopedAdmin(CommandAdmin):
    read_permission = "resources.read"
    manage_permission = "resources.manage"

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .filter(
                organization_id__in=authorized_organization_ids(
                    request.user.pk, self.read_permission
                )
            )
        )

    def has_module_permission(self, request):
        return self.has_view_permission(request) or self.has_add_permission(request)

    def has_view_permission(self, request, obj=None):
        ids = authorized_organization_ids(request.user.pk, self.read_permission)
        return bool(ids) if obj is None else obj.organization_id in ids

    def has_add_permission(self, request):
        return bool(authorized_organization_ids(request.user.pk, self.manage_permission))

    def has_change_permission(self, request, obj=None):
        ids = authorized_organization_ids(request.user.pk, self.manage_permission)
        return bool(ids) if obj is None else obj.organization_id in ids


class NamedCreateForm(forms.Form):
    organization = forms.ChoiceField()
    code = forms.CharField(
        max_length=32, help_text="Unique organization code; cannot change later."
    )
    name = forms.CharField(max_length=200)


def member_choices(actor_id, ids):
    choices = [("", "Choose an existing member (optional)")]
    for oid in ids:
        page = 1
        scope = resolve_scope(actor_id, oid)
        org_name = get_organization(actor_id, oid).name
        while True:
            result = service.resource_choices(scope, "members", page, 100)
            choices.extend((str(row.id), f"{org_name} / {row.label}") for row in result.results)
            if page * 100 >= result.count:
                break
            page += 1
    return choices


class MemberOrPersonForm(NamedCreateForm):
    membership_id = forms.ChoiceField(
        required=False, widget=SearchableSelect, label="Existing member"
    )
    code = forms.CharField(max_length=32, required=False)
    name = forms.CharField(max_length=200, required=False)

    def clean(self):
        data = super().clean()
        if data.get("membership_id"):
            if data.get("code") or data.get("name"):
                raise forms.ValidationError(
                    "Select a member OR enter a no-login person's code and name."
                )
        elif not data.get("name"):
            raise forms.ValidationError(
                "Choose an existing member, or enter a name for a no-login resource. "
                "Code is optional."
            )
        return data


class NamedChangeForm(forms.Form):
    name = forms.CharField(max_length=200)
    status = forms.ChoiceField()
    version = forms.IntegerField(widget=forms.HiddenInput)
    reason = forms.CharField(max_length=500)


class NamedAdmin(ScopedAdmin):
    def command_form(self, request, obj, data):
        name = "display_name" if self.model is Resource else "name"
        if obj:
            form = NamedChangeForm(
                data,
                initial={"name": getattr(obj, name), "status": obj.status, "version": obj.version},
            )
            form.fields["status"].choices = self.model._meta.get_field("status").choices
            form.fields[
                "status"
            ].help_text = (
                "History and existing assignments remain; new assignments require active status."
            )
            return form
        form = MemberOrPersonForm(data) if self.model is Resource else NamedCreateForm(data)
        if self.model is Resource:
            eligible = (
                set(authorized_organization_ids(request.user.pk, "resources.manage"))
                & set(authorized_organization_ids(request.user.pk, "resources.read"))
                & set(authorized_organization_ids(request.user.pk, "resources.link_identity"))
                & set(authorized_organization_ids(request.user.pk, "memberships.read"))
            )
            form.fields["membership_id"].choices = member_choices(request.user.pk, eligible)
        ids = authorized_organization_ids(request.user.pk, self.manage_permission)
        form.fields["organization"].choices = [
            (str(oid), get_organization(request.user.pk, oid).name) for oid in ids
        ]
        return form

    def execute(self, request, obj, data):
        resource = self.model is Resource
        if resource and not obj and data.get("membership_id"):
            service.add_resource_from_member(
                resolve_scope(request.user.pk, data["organization"]), data["membership_id"]
            )
            return
        data.pop("membership_id", None)
        if resource:
            data["display_name"] = data.pop("name")
        if obj:
            command = service.update_resource if resource else service.update_team
            command(resolve_scope(request.user.pk, obj.organization_id), obj.pk, **data)
        else:
            command = service.create_resource if resource else service.create_team
            command(resolve_scope(request.user.pk, data.pop("organization")), **data)


@admin.register(Resource)
class ResourceAdmin(NamedAdmin):
    list_display = ("display_name", "code", "status", "version")
    search_fields = ("display_name", "code")
    list_filter = ("status",)


@admin.register(Team)
class TeamAdmin(NamedAdmin):
    read_permission = "teams.read"
    manage_permission = "teams.manage"
    list_display = ("name", "code", "status", "version")
    search_fields = ("name", "code")
    list_filter = ("status",)


class LinkCreateForm(forms.Form):
    resource = forms.ModelChoiceField(queryset=Resource.objects.none())
    membership_id = forms.ChoiceField(label="Organization member", widget=SearchableSelect)
    version = forms.IntegerField(widget=forms.HiddenInput, required=False)
    reason = forms.CharField(max_length=500)


class LinkEndForm(forms.Form):
    version = forms.IntegerField(widget=forms.HiddenInput)
    reason = forms.CharField(
        max_length=500,
        help_text="Ends this login link now. The person and earlier link history remain.",
    )


@admin.register(ResourceIdentityLink)
class IdentityLinkAdmin(ScopedAdmin):
    manage_permission = "resources.link_identity"
    list_display = ("resource", "membership_id", "started_at", "ended_at")
    list_select_related = ("resource",)

    def has_add_permission(self, request):
        return bool(
            set(authorized_organization_ids(request.user.pk, self.manage_permission))
            & set(authorized_organization_ids(request.user.pk, "memberships.read"))
        )

    def command_form(self, request, obj, data):
        if obj:
            return LinkEndForm(data, initial={"version": obj.resource.version})
        ids = set(authorized_organization_ids(request.user.pk, self.manage_permission)) & set(
            authorized_organization_ids(request.user.pk, "memberships.read")
        )
        form = LinkCreateForm(data)
        form.fields["resource"].queryset = Resource.objects.filter(
            organization_id__in=ids, status="active"
        ).order_by("display_name")
        choices = []
        for oid in ids:
            org = get_organization(request.user.pk, oid)
            page = 1
            while True:
                members = list_memberships(request.user.pk, oid, page, 100, "active")
                choices.extend(
                    (str(m.id), f"{org.name} / {m.display_name or m.username} (@{m.username})")
                    for m in members.results
                )
                if page * 100 >= members.count:
                    break
                page += 1
        form.fields["membership_id"].choices = choices
        from django.core import signing

        form.fields["revisions"] = forms.CharField(
            widget=forms.HiddenInput,
            initial=signing.dumps({str(r.id): r.version for r in form.fields["resource"].queryset}),
        )
        return form

    def execute(self, request, obj, data):
        if obj:
            service.end_identity_link(
                resolve_scope(request.user.pk, obj.organization_id), obj.resource_id, obj.pk, **data
            )
        else:
            from django.core import signing

            resource = data.pop("resource")
            try:
                versions = signing.loads(data.pop("revisions"))
                data["version"] = versions[str(resource.id)]
            except (signing.BadSignature, KeyError):
                raise PermissionDenied("Reload the link form.") from None
            service.link_identity(
                resolve_scope(request.user.pk, resource.organization_id), resource.pk, **data
            )


class AssignmentCreateForm(forms.Form):
    team = forms.ModelChoiceField(queryset=Team.objects.none())
    resource = forms.ModelChoiceField(
        queryset=Resource.objects.none(),
        label="Existing resource",
        required=False,
        widget=SearchableSelect,
    )
    membership_id = forms.ChoiceField(
        required=False, label="Existing member", widget=SearchableSelect
    )
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}),
        help_text="Today or later in the organization timezone; inclusive.",
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
        help_text="Exclusive end: no longer in the team on this date. Blank means ongoing.",
    )


class AssignmentEndForm(forms.Form):
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}),
        help_text="Today or later, strictly after start; exclusive end.",
    )
    version = forms.IntegerField(widget=forms.HiddenInput)
    reason = forms.CharField(max_length=500)


@admin.register(TeamMembership)
class TeamMembershipAdmin(ScopedAdmin):
    read_permission = "teams.read"
    manage_permission = "teams.manage"
    list_display = ("team", "resource", "start_date", "end_date", "version")
    list_select_related = ("team", "resource")

    def has_add_permission(self, request):
        return bool(
            set(authorized_organization_ids(request.user.pk, self.manage_permission))
            & set(authorized_organization_ids(request.user.pk, "resources.read"))
        )

    def command_form(self, request, obj, data):
        if obj:
            return AssignmentEndForm(
                data, initial={"end_date": obj.end_date, "version": obj.version}
            )
        form = AssignmentCreateForm(data)
        ids = set(authorized_organization_ids(request.user.pk, self.manage_permission)) & set(
            authorized_organization_ids(request.user.pk, "resources.read")
        )
        form.fields["team"].queryset = Team.objects.filter(
            organization_id__in=ids, status="active"
        ).order_by("name")
        form.fields["resource"].queryset = Resource.objects.filter(
            organization_id__in=ids, status="active"
        ).order_by("display_name")
        member_ids = ids & set(authorized_organization_ids(request.user.pk, "memberships.read"))
        form.fields["membership_id"].choices = member_choices(request.user.pk, member_ids)
        return form

    def execute(self, request, obj, data):
        if obj:
            service.end_team_membership(
                resolve_scope(request.user.pk, obj.organization_id), obj.team_id, obj.pk, **data
            )
        else:
            team = data.pop("team")
            resource = data.pop("resource")
            service.assign_team_member(
                resolve_scope(request.user.pk, team.organization_id),
                team.pk,
                resource.pk if resource else None,
                **{**data, "membership_id": data.get("membership_id") or None},
            )


@admin.register(ResourceChangeEvent)
class ResourceEventAdmin(ReadOnlyAdmin):
    list_display = ("entity_type", "action", "occurred_at")

    def get_queryset(self, request):
        resource_ids = authorized_organization_ids(request.user.pk, "resources.read")
        team_ids = authorized_organization_ids(request.user.pk, "teams.read")
        from django.db.models import Q

        return (
            super()
            .get_queryset(request)
            .filter(
                Q(organization_id__in=resource_ids, entity_type="resource")
                | Q(organization_id__in=team_ids, entity_type__in=["team", "teammembership"])
            )
        )

    def has_module_permission(self, request):
        return bool(
            authorized_organization_ids(request.user.pk, "resources.read")
            or authorized_organization_ids(request.user.pk, "teams.read")
        )

    def has_view_permission(self, request, obj=None):
        if obj is None:
            return self.has_module_permission(request)
        key = "resources.read" if obj.entity_type == "resource" else "teams.read"
        return obj.organization_id in authorized_organization_ids(request.user.pk, key)
