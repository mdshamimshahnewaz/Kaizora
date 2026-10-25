from django import forms
from django.contrib import admin

from common.admin import CommandAdmin, ReadOnlyAdmin

from . import interfaces as service
from .models import Membership, MembershipStatusEvent, Organization, OrganizationChangeEvent


class OrganizationCreateForm(forms.Form):
    name = forms.CharField(max_length=200)
    timezone = forms.CharField(max_length=64, initial="Asia/Dhaka")
    owner_username = forms.CharField(
        max_length=150, help_text="Exact username of the first active owner."
    )


class OwnerTransferForm(forms.Form):
    target_membership_id = forms.ModelChoiceField(
        queryset=Membership.objects.none(), label="New owner"
    )
    version = forms.IntegerField(widget=forms.HiddenInput)
    reason = forms.CharField(max_length=500)


class MembershipCreateForm(forms.Form):
    organization = forms.ModelChoiceField(queryset=Organization.objects.none())
    username = forms.CharField(max_length=150, help_text="Exact existing active username.")


class MembershipChangeForm(forms.Form):
    status = forms.ChoiceField(choices=Membership.Status.choices)
    version = forms.IntegerField(widget=forms.HiddenInput)
    reason = forms.CharField(max_length=500)


@admin.register(Organization)
class OrganizationAdmin(CommandAdmin):
    list_display = ("name", "timezone", "status", "version")

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .filter(pk__in=service.authorized_organization_ids(request.user.pk))
        )

    def has_module_permission(self, request):
        return self.has_add_permission(request) or self.has_view_permission(request)

    def has_view_permission(self, request, obj=None):
        return bool(service.authorized_organization_ids(request.user.pk))

    def has_add_permission(self, request):
        return service.provisioning_capability(request.user.pk)

    def has_change_permission(self, request, obj=None):
        if obj is None:
            return self.has_view_permission(request)
        return service.resolve_scope(request.user.pk, obj.pk).is_owner

    def command_form(self, request, obj, data):
        if obj is None:
            return OrganizationCreateForm(data)
        form = OwnerTransferForm(data, initial={"version": obj.version})
        form.fields["target_membership_id"].queryset = (
            Membership.objects.filter(organization=obj, status="active", user__is_active=True)
            .exclude(user=request.user)
            .select_related("user")
        )
        form.fields["target_membership_id"].label_from_instance = lambda member: (
            member.user.get_username()
        )
        form.fields["reason"].help_text = "Transfer ownership: you will stop being an owner."
        return form

    def execute(self, request, obj, data):
        if obj is None:
            service.create_organization(request.user.pk, **data)
        else:
            service.transfer_owner(
                request.user.pk,
                obj.pk,
                data["target_membership_id"].pk,
                data["version"],
                data["reason"],
            )


@admin.register(Membership)
class MembershipAdmin(CommandAdmin):
    list_display = ("organization", "user", "status", "is_owner", "version")
    list_filter = ("status", "is_owner")

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .filter(
                organization_id__in=service.authorized_organization_ids(
                    request.user.pk, "memberships.read"
                )
            )
            .select_related("organization", "user")
        )

    def has_module_permission(self, request):
        return self.has_view_permission(request) or self.has_add_permission(request)

    def has_view_permission(self, request, obj=None):
        return bool(service.authorized_organization_ids(request.user.pk, "memberships.read"))

    def has_add_permission(self, request):
        return bool(service.authorized_organization_ids(request.user.pk, "memberships.manage"))

    def has_change_permission(self, request, obj=None):
        ids = service.authorized_organization_ids(request.user.pk, "memberships.manage")
        return bool(ids) if obj is None else obj.organization_id in ids

    def command_form(self, request, obj, data):
        if obj:
            return MembershipChangeForm(
                data, initial={"status": obj.status, "version": obj.version}
            )
        form = MembershipCreateForm(data)
        form.fields["organization"].queryset = Organization.objects.filter(
            pk__in=service.authorized_organization_ids(request.user.pk, "memberships.manage")
        )
        return form

    def execute(self, request, obj, data):
        if obj:
            service.change_membership(request.user.pk, obj.organization_id, obj.pk, **data)
        else:
            service.add_membership(
                request.user.pk, data["organization"].pk, username=data["username"]
            )


admin.site.register(MembershipStatusEvent, ReadOnlyAdmin)
admin.site.register(OrganizationChangeEvent, ReadOnlyAdmin)
