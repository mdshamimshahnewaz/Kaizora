from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm

from common.admin import CommandAdmin, ReadOnlyAdmin
from modules.organizations.interfaces import (
    authorized_organization_ids,
    get_organization,
    list_memberships,
)

from . import interfaces as service
from .catalog import ALL_KEYS
from .models import (
    AccountChangeEvent,
    AccountPreferences,
    GrantChangeEvent,
    OrganizationRole,
    RoleAssignment,
    RolePermission,
    User,
)


class AccountUserChangeForm(UserChangeForm):
    account_version = forms.IntegerField(widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            preferences = AccountPreferences.objects.filter(user=self.instance).first()
            self.fields["account_version"].initial = preferences.version if preferences else 1

    def clean(self):
        cleaned = super().clean()
        if self.instance.pk:
            # UserAdmin wraps change-form validation and save in one transaction.
            User.objects.select_for_update().get(pk=self.instance.pk)
            preferences = AccountPreferences.objects.filter(user=self.instance).first()
            version = preferences.version if preferences else 1
            if cleaned.get("account_version") != version:
                raise forms.ValidationError(
                    "This account changed since you opened it. Reload before saving."
                )
        return cleaned


class AccountUserAdmin(UserAdmin):
    form = AccountUserChangeForm
    fieldsets = (*UserAdmin.fieldsets, (None, {"fields": ("account_version",)}))

    def save_model(self, request, obj, form, change):
        if change and {"first_name", "last_name"}.intersection(form.changed_data):
            from django.db import transaction

            from .account import update_account
            from .models import AccountPreferences

            with transaction.atomic():
                User.objects.select_for_update().get(pk=obj.pk)
                preferences, _ = AccountPreferences.objects.get_or_create(user=obj)
                update_account(
                    request.user.pk,
                    preferences.version,
                    target_user_id=obj.pk,
                    first_name=obj.first_name,
                    last_name=obj.last_name,
                )
                super().save_model(request, obj, form, change)
        else:
            super().save_model(request, obj, form, change)


admin.site.register(User, AccountUserAdmin)


class RoleForm(forms.Form):
    organization = forms.ChoiceField()
    name = forms.CharField(max_length=200)
    scope_kind = forms.ChoiceField(
        choices=[("organization", "Organization"), ("project", "Project")]
    )
    permissions = forms.MultipleChoiceField(
        choices=[(key, key) for key in sorted(ALL_KEYS)],
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )
    status = forms.ChoiceField(
        choices=[("active", "Active"), ("archived", "Archived")], initial="active"
    )
    version = forms.IntegerField(widget=forms.HiddenInput, required=False)
    reason = forms.CharField(max_length=500, required=False)


class AssignmentForm(forms.Form):
    organization = forms.ChoiceField()
    membership_id = forms.ChoiceField(label="Member")
    role_id = forms.ModelChoiceField(queryset=OrganizationRole.objects.none(), label="Role")
    reason = forms.CharField(max_length=500)


class RevokeForm(forms.Form):
    version = forms.IntegerField(widget=forms.HiddenInput)
    reason = forms.CharField(
        max_length=500, help_text="Saving revokes this assignment and retains its history."
    )


class ScopedAccessAdmin(CommandAdmin):
    write_permission = "roles.manage"

    def scopes(self, request, permission):
        return authorized_organization_ids(request.user.pk, permission)

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .filter(organization_id__in=self.scopes(request, "roles.read"))
        )

    def has_module_permission(self, request):
        return self.has_view_permission(request) or self.has_add_permission(request)

    def has_view_permission(self, request, obj=None):
        return bool(self.scopes(request, "roles.read"))

    def has_add_permission(self, request):
        return bool(self.scopes(request, self.write_permission))

    def has_change_permission(self, request, obj=None):
        ids = self.scopes(request, self.write_permission)
        return bool(ids) if obj is None else obj.organization_id in ids

    def organization_choices(self, request):
        return [
            (str(pk), get_organization(request.user.pk, pk).name)
            for pk in self.scopes(request, self.write_permission)
        ]


@admin.register(OrganizationRole)
class RoleAdmin(ScopedAccessAdmin):
    list_display = ("name", "organization", "scope_kind", "status", "version")

    def command_form(self, request, obj, data):
        initial = (
            {}
            if obj is None
            else {
                "name": obj.name,
                "permissions": list(obj.permission_records.values_list("key", flat=True)),
                "status": obj.status,
                "version": obj.version,
            }
        )
        form = RoleForm(data, initial=initial)
        if obj:
            del form.fields["organization"]
            del form.fields["scope_kind"]
            form.fields["version"].required = True
            form.fields["reason"].required = True
        else:
            form.fields["organization"].choices = self.organization_choices(request)
            for field in ["status", "version", "reason"]:
                del form.fields[field]
        return form

    def execute(self, request, obj, data):
        if obj:
            service.update_role(request.user.pk, obj.organization_id, obj.pk, **data)
        else:
            service.create_role(request.user.pk, data.pop("organization"), **data)


@admin.register(RoleAssignment)
class AssignmentAdmin(ScopedAccessAdmin):
    write_permission = "roles.assign"
    list_display = ("organization", "membership", "role", "started_at", "ended_at")

    def command_form(self, request, obj, data):
        if obj:
            return RevokeForm(data, initial={"version": obj.version})
        form = AssignmentForm(data)
        choices = self.organization_choices(request)
        form.fields["organization"].choices = choices
        readable = set(self.scopes(request, "memberships.read"))
        members = []
        for org_id, name in choices:
            from uuid import UUID

            if UUID(org_id) not in readable:
                continue
            page = 1
            while True:
                result = list_memberships(request.user.pk, org_id, page, 100, "active")
                members.extend(
                    (str(member.id), f"{name} — {member.username}") for member in result.results
                )
                if page * 100 >= result.count:
                    break
                page += 1
        form.fields["membership_id"].choices = members
        form.fields["role_id"].queryset = OrganizationRole.objects.filter(
            organization_id__in=self.scopes(request, "roles.read"),
            status="active",
            scope_kind="organization",
        ).select_related("organization")
        form.fields["role_id"].label_from_instance = lambda role: (
            f"{role.organization} — {role.name}"
        )
        return form

    def execute(self, request, obj, data):
        if obj:
            service.revoke_assignment(request.user.pk, obj.organization_id, obj.pk, **data)
        else:
            service.assign_role(
                request.user.pk,
                data["organization"],
                data["membership_id"],
                data["role_id"].pk,
                data["reason"],
            )


admin.site.register(RolePermission, ReadOnlyAdmin)
admin.site.register(GrantChangeEvent, ReadOnlyAdmin)


class AccountForm(forms.Form):
    user = forms.ModelChoiceField(queryset=User.objects.all())
    theme = forms.ChoiceField(
        choices=[
            ("", "Use device default"),
            ("light", "Light"),
            ("dark", "Dark"),
            ("system", "System"),
        ],
        required=False,
    )
    timezone = forms.CharField(
        max_length=100,
        required=False,
        help_text="IANA name, e.g. Asia/Dhaka. Blank inherits the organization timezone.",
    )
    version = forms.IntegerField(widget=forms.HiddenInput, initial=1)


@admin.register(AccountPreferences)
class AccountPreferencesAdmin(CommandAdmin):
    list_display = ("user", "theme", "timezone", "version")
    search_fields = ("user__username",)

    def has_add_permission(self, request):
        return request.user.has_perm("identity.change_user")

    def has_change_permission(self, request, obj=None):
        return request.user.has_perm("identity.change_user")

    def has_view_permission(self, request, obj=None):
        return request.user.has_perm("identity.view_user")

    def command_form(self, request, obj, data):
        form = AccountForm(
            data,
            initial={
                "user": obj.user_id,
                "theme": obj.theme or "",
                "timezone": obj.timezone or "",
                "version": obj.version,
            }
            if obj
            else {},
        )
        if obj:
            del form.fields["user"]
        return form

    def execute(self, request, obj, data):
        from .account import update_account

        update_account(
            request.user.pk,
            data["version"],
            target_user_id=obj.user_id if obj else data["user"].pk,
            preferences={"theme": data["theme"] or None, "timezone": data["timezone"] or None},
        )


admin.site.register(AccountChangeEvent, ReadOnlyAdmin)
