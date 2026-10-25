from django import forms
from django.contrib import admin
from rest_framework.exceptions import APIException

from common.admin import CommandAdmin, ReadOnlyAdmin
from common.widgets import SearchableSelect
from modules.organizations.interfaces import (
    authorized_organization_ids,
    get_organization,
    resolve_scope,
)

from . import interfaces as service
from .models import Project, ProjectAccess, ProjectChangeEvent, ProjectWorker


def _all_options(scope, kind, project_id=None):
    page = 1
    result = []
    while True:
        batch = service.assignment_options(scope, kind, page, 100, project_id=project_id)
        result.extend(batch.results)
        if len(result) >= batch.count:
            return result
        page += 1


def _can(request, obj, permission):
    _visible(request)
    return permission in request._project_capabilities.get(obj.id, ())


def _visible(request):
    if not hasattr(request, "_project_capabilities"):
        capabilities = {}
        for org in authorized_organization_ids(request.user.pk):
            try:
                records = service.get_admin_project_capabilities(
                    resolve_scope(request.user.pk, org)
                )
            except APIException:
                continue
            capabilities.update({record.id: record.capabilities for record in records})
        request._project_capabilities = capabilities
    return tuple(request._project_capabilities)


class CreateProjectForm(forms.Form):
    organization = forms.ChoiceField()
    code = forms.CharField(max_length=32, help_text="Immutable organization-unique code.")
    name = forms.CharField(max_length=200)
    type = forms.ChoiceField(choices=[("delivery", "Delivery"), ("operations", "Operations")])
    client_id = forms.ChoiceField(required=False)
    initial_manager_membership_id = forms.ChoiceField(
        widget=SearchableSelect, help_text="Choose an active login member in the same organization."
    )
    initial_manager_role_id = forms.ChoiceField(
        help_text="Choose a delegable manager role. Create roles in Identity first."
    )
    description = forms.CharField(max_length=4000, required=False, widget=forms.Textarea)
    start_date = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    target_end_date = forms.DateField(
        required=False, widget=forms.DateInput(attrs={"type": "date"})
    )


class ChangeProjectForm(forms.Form):
    action = forms.ChoiceField(
        choices=[
            ("edit", "Edit details"),
            ("active", "Activate / reopen"),
            ("completed", "Complete"),
            ("archived", "Archive"),
            ("draft", "Restore to draft"),
        ]
    )
    name = forms.CharField(max_length=200, required=False)
    description = forms.CharField(max_length=4000, required=False, widget=forms.Textarea)
    start_date = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    target_end_date = forms.DateField(
        required=False, widget=forms.DateInput(attrs={"type": "date"})
    )
    version = forms.IntegerField(widget=forms.HiddenInput)
    reason = forms.CharField(
        max_length=500,
        help_text="Archiving prevents edits and new grants; existing history remains readable.",
    )


@admin.register(Project)
class ProjectAdmin(CommandAdmin):
    list_display = ("name", "code", "type", "status", "version")
    list_filter = ("type", "status")
    search_fields = ("name", "code")

    def get_queryset(self, request):
        return super().get_queryset(request).filter(id__in=_visible(request))

    def has_module_permission(self, request):
        return self.has_view_permission(request) or self.has_add_permission(request)

    def has_view_permission(self, request, obj=None):
        return bool(_visible(request)) if obj is None else _can(request, obj, "projects.read")

    def has_add_permission(self, request):
        return bool(authorized_organization_ids(request.user.pk, "projects.create"))

    def has_change_permission(self, request, obj=None):
        if obj is None:
            return self.has_view_permission(request)
        return any(
            _can(request, obj, key)
            for key in (
                "projects.manage",
                "projects.transition",
                "projects.restore",
                "projects.reopen",
            )
        )

    def command_form(self, request, obj, data):
        if obj:
            form = ChangeProjectForm(
                data,
                initial={
                    "action": "edit",
                    **{
                        key: getattr(obj, key)
                        for key in (
                            "name",
                            "description",
                            "start_date",
                            "target_end_date",
                            "version",
                        )
                    },
                },
            )
            allowed = []
            if obj.status != "archived" and _can(request, obj, "projects.manage"):
                allowed.append(("edit", "Edit details"))
            targets = {
                "draft": ["active", "archived"],
                "active": ["completed", "archived"],
                "completed": ["active", "archived"],
                "archived": ["draft"],
            }
            for target in targets[obj.status]:
                permission = (
                    "projects.restore"
                    if obj.status == "archived"
                    else "projects.reopen"
                    if obj.status == "completed" and target == "active"
                    else "projects.transition"
                )
                if _can(request, obj, permission):
                    allowed.append((target, f"Move to {target}"))
            form.fields["action"].choices = allowed
            form.initial["action"] = allowed[0][0] if allowed else ""
            return form
        form = CreateProjectForm(data)
        organizations, members, roles, clients = [], [], [], [("", "Internal project — no client")]
        for org_id in authorized_organization_ids(request.user.pk, "projects.create"):
            scope = resolve_scope(request.user.pk, org_id)
            name = get_organization(request.user.pk, org_id).name
            organizations.append((str(org_id), name))
            members.extend(
                (str(m.id), f"{name} / {m.display_name or m.username}")
                for m in _all_options(scope, "members")
            )
            roles.extend((str(r.id), f"{name} / {r.name}") for r in _all_options(scope, "roles"))
            clients.extend(
                (str(c.id), f"{name} / {c.name}") for c in _all_options(scope, "clients")
            )
        for key, choices in [
            ("organization", organizations),
            ("initial_manager_membership_id", members),
            ("initial_manager_role_id", roles),
            ("client_id", clients),
        ]:
            form.fields[key].choices = choices
        return form

    def execute(self, request, obj, data):
        if obj:
            scope = resolve_scope(request.user.pk, obj.organization_id)
            action = data.pop("action")
            if action == "edit":
                service.update_project(scope, obj.id, **data)
            else:
                service.transition_project(
                    scope,
                    obj.id,
                    target_status=action,
                    version=data["version"],
                    reason=data["reason"],
                )
        else:
            scope = resolve_scope(request.user.pk, data.pop("organization"))
            data["client_id"] = data["client_id"] or None
            service.create_project(scope, **data)


class GrantForm(forms.Form):
    project = forms.ModelChoiceField(queryset=Project.objects.none())
    membership_id = forms.ChoiceField(widget=SearchableSelect)
    role_id = forms.ChoiceField()
    reason = forms.CharField(max_length=500)


class EndForm(forms.Form):
    version = forms.IntegerField(widget=forms.HiddenInput)
    reason = forms.CharField(
        max_length=500,
        help_text="Ends access now; historical work and the grant remain attributable.",
    )


@admin.register(ProjectAccess)
class ProjectAccessAdmin(CommandAdmin):
    list_display = ("project", "started_at", "ended_at", "version")
    list_select_related = ("project",)

    def get_queryset(self, request):
        ids = [
            p.id
            for p in Project.objects.filter(id__in=_visible(request))
            if _can(request, p, "projects.access.read")
        ]
        return super().get_queryset(request).filter(project_id__in=ids)

    def has_module_permission(self, request):
        return self.has_view_permission(request) or self.has_add_permission(request)

    def has_view_permission(self, request, obj=None):
        return (
            self.get_queryset(request).exists()
            if obj is None
            else _can(request, obj.project, "projects.access.read")
        )

    def has_add_permission(self, request):
        return any(
            _can(request, p, "projects.access.manage")
            for p in Project.objects.filter(id__in=_visible(request))
        )

    def has_change_permission(self, request, obj=None):
        return (
            self.has_add_permission(request)
            if obj is None
            else obj.ended_at is None and _can(request, obj.project, "projects.access.manage")
        )

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context)
        context = getattr(response, "context_data", None)
        if context and "cl" in context:
            grouped = {}
            for row in context["cl"].result_list:
                grouped.setdefault(row.organization_id, []).append(row)
            labels = {}
            for org_id, rows in grouped.items():
                scope = resolve_scope(request.user.pk, org_id)
                for offset in range(0, len(rows), 100):
                    labels.update(
                        {
                            item.id: item
                            for item in service._access_dtos(scope, rows[offset : offset + 100])
                        }
                    )
            request._project_access_labels = labels
        return response

    def get_list_display(self, request):
        def member(obj):
            return request._project_access_labels[obj.id].member_name

        def role(obj):
            return request._project_access_labels[obj.id].role_name

        return ("project", member, role, "started_at", "ended_at", "version")

    def command_form(self, request, obj, data):
        if obj:
            return EndForm(data, initial={"version": obj.version})
        form = GrantForm(data)
        projects = [
            p
            for p in Project.objects.filter(
                id__in=_visible(request), status__in=["draft", "active", "completed"]
            )
            if _can(request, p, "projects.access.manage")
        ]
        form.fields["project"].queryset = Project.objects.filter(id__in=[p.id for p in projects])
        members, roles = {}, {}
        member_organizations = set()
        role_choices = {}
        for project in projects:
            scope = resolve_scope(request.user.pk, project.organization_id)
            org_name = get_organization(request.user.pk, project.organization_id).name
            if project.organization_id not in member_organizations:
                for member in _all_options(scope, "members", project.id):
                    members[str(member.id)] = (
                        f"{org_name} / {member.display_name or member.username}"
                    )
                member_organizations.add(project.organization_id)
            role_key = (
                project.organization_id,
                tuple(sorted(request._project_capabilities[project.id])),
            )
            if role_key not in role_choices:
                role_choices[role_key] = _all_options(scope, "roles", project.id)
            for role in role_choices[role_key]:
                roles[str(role.id)] = f"{org_name} / {role.name}"
        form.fields["membership_id"].choices = list(members.items())
        form.fields["role_id"].choices = list(roles.items())
        return form

    def execute(self, request, obj, data):
        if obj:
            service.end_access(
                resolve_scope(request.user.pk, obj.organization_id), obj.project_id, obj.id, **data
            )
        else:
            project = data.pop("project")
            service.grant_access(
                resolve_scope(request.user.pk, project.organization_id), project.id, **data
            )


@admin.register(ProjectChangeEvent)
class ProjectChangeEventAdmin(ReadOnlyAdmin):
    list_display = ("project", "action", "occurred_at", "before_version", "after_version")

    def get_queryset(self, request):
        ids = [
            p.id
            for p in Project.objects.filter(id__in=_visible(request))
            if _can(request, p, "projects.access.read")
        ]
        return super().get_queryset(request).filter(project_id__in=ids)

    def has_module_permission(self, request):
        return self.get_queryset(request).exists()

    def has_view_permission(self, request, obj=None):
        return (
            self.has_module_permission(request)
            if obj is None
            else _can(request, obj.project, "projects.access.read")
        )


class WorkerCreateForm(forms.Form):
    project = forms.ModelChoiceField(queryset=Project.objects.none(), widget=SearchableSelect)
    membership_id = forms.ChoiceField(
        required=False, widget=SearchableSelect, label="Existing member"
    )
    resource_id = forms.ChoiceField(
        required=False,
        widget=SearchableSelect,
        label="Existing resource (including no-login workers)",
    )
    reason = forms.CharField(max_length=500)


@admin.register(ProjectWorker)
class ProjectWorkerAdmin(CommandAdmin):
    list_display = ("project", "resource_name", "started_at", "ended_at", "version")
    list_select_related = ("project",)

    def get_queryset(self, request):
        return super().get_queryset(request).filter(project_id__in=_visible(request))

    def has_module_permission(self, request):
        return bool(_visible(request))

    def has_view_permission(self, request, obj=None):
        return (
            bool(_visible(request)) if obj is None else _can(request, obj.project, "projects.read")
        )

    def has_add_permission(self, request):
        _visible(request)
        return any("projects.manage" in keys for keys in request._project_capabilities.values())

    def has_change_permission(self, request, obj=None):
        return (
            self.has_add_permission(request)
            if obj is None
            else obj.ended_at is None and _can(request, obj.project, "projects.manage")
        )

    def command_form(self, request, obj, data):
        if obj:
            form = EndForm(data, initial={"version": obj.version})
            form.fields[
                "reason"
            ].help_text = (
                "Ends workforce assignment now; history remains. Login/project access is unchanged."
            )
            return form
        form = WorkerCreateForm(data)
        projects = [
            p
            for p in Project.objects.filter(id__in=_visible(request)).exclude(status="archived")
            if _can(request, p, "projects.manage")
        ]
        form.fields["project"].queryset = Project.objects.filter(id__in=[p.id for p in projects])
        from modules.resources.interfaces import assignment_choices

        for field, kind in (("membership_id", "members"), ("resource_id", "resources")):
            choices = [("", "Choose one member OR resource")]
            for oid in {p.organization_id for p in projects}:
                scope = resolve_scope(request.user.pk, oid)
                org = get_organization(request.user.pk, oid)
                page = 1
                while True:
                    batch = assignment_choices(scope, kind, page, 100)
                    choices.extend(
                        (str(row.id), f"{org.name} / {row.label}") for row in batch.results
                    )
                    if page * 100 >= batch.count:
                        break
                    page += 1
            form.fields[field].choices = choices
        return form

    def execute(self, request, obj, data):
        if obj:
            service.end_worker(
                resolve_scope(request.user.pk, obj.organization_id), obj.project_id, obj.pk, **data
            )
        else:
            project = data.pop("project")
            service.add_worker(
                resolve_scope(request.user.pk, project.organization_id),
                project.pk,
                **{key: value or None for key, value in data.items()},
            )
