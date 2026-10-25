from django import forms
from django.contrib import admin

from common.admin import CommandAdmin, ReadOnlyAdmin
from modules.organizations.interfaces import (
    authorized_organization_ids,
    get_organization,
    resolve_scope,
)

from . import interfaces as service
from .models import Client, ClientChangeEvent, Contact, ContactChangeEvent


class ClientCreateForm(forms.Form):
    organization = forms.ChoiceField()
    code = forms.CharField(
        max_length=32, help_text="Unique within the organization; cannot change."
    )
    name = forms.CharField(max_length=200)


class ClientChangeForm(forms.Form):
    name = forms.CharField(max_length=200)
    status = forms.ChoiceField(
        choices=Client.Status.choices,
        help_text="Archiving preserves history and prevents new project links.",
    )
    version = forms.IntegerField(widget=forms.HiddenInput)
    reason = forms.CharField(max_length=500)


class ContactCreateForm(forms.Form):
    client = forms.ModelChoiceField(queryset=Client.objects.none())
    name = forms.CharField(max_length=200)
    email = forms.EmailField(required=False)
    phone = forms.CharField(max_length=50, required=False)
    position = forms.CharField(max_length=200, required=False)


class ContactChangeForm(forms.Form):
    name = forms.CharField(max_length=200)
    email = forms.EmailField(required=False)
    phone = forms.CharField(max_length=50, required=False)
    position = forms.CharField(max_length=200, required=False)
    status = forms.ChoiceField(choices=Contact.Status.choices)
    version = forms.IntegerField(widget=forms.HiddenInput)
    reason = forms.CharField(
        max_length=500,
        help_text="Business reason only; do not copy contact personal data into history.",
    )


class ScopedCommandAdmin(CommandAdmin):
    read_permission = "clients.read"
    manage_permission = "clients.manage"

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


@admin.register(Client)
class ClientAdmin(ScopedCommandAdmin):
    list_display = ("name", "code", "status", "version")
    search_fields = ("name", "code")
    list_filter = ("status",)

    def command_form(self, request, obj, data):
        if obj:
            return ClientChangeForm(
                data, initial={"name": obj.name, "status": obj.status, "version": obj.version}
            )
        form = ClientCreateForm(data)
        ids = authorized_organization_ids(request.user.pk, self.manage_permission)
        form.fields["organization"].choices = [
            (str(oid), get_organization(request.user.pk, oid).name) for oid in ids
        ]
        return form

    def execute(self, request, obj, data):
        if obj:
            service.update_client(
                resolve_scope(request.user.pk, obj.organization_id), obj.id, **data
            )
        else:
            scope = resolve_scope(request.user.pk, data.pop("organization"))
            service.create_client(scope, **data)


@admin.register(Contact)
class ContactAdmin(ScopedCommandAdmin):
    read_permission = "contacts.read"
    manage_permission = "contacts.manage"
    list_display = ("name", "client", "position", "status", "version")
    list_filter = ("status",)
    search_fields = ("name", "client__name")
    list_select_related = ("client",)

    def command_form(self, request, obj, data):
        if obj:
            return ContactChangeForm(
                data,
                initial={
                    field: getattr(obj, field)
                    for field in ("name", "email", "phone", "position", "status", "version")
                },
            )
        form = ContactCreateForm(data)
        form.fields["client"].queryset = Client.objects.filter(
            status="active",
            organization_id__in=authorized_organization_ids(
                request.user.pk, self.manage_permission
            ),
        ).order_by("name")
        return form

    def execute(self, request, obj, data):
        if obj:
            service.update_contact(
                resolve_scope(request.user.pk, obj.organization_id), obj.client_id, obj.id, **data
            )
        else:
            client = data.pop("client")
            service.create_contact(
                resolve_scope(request.user.pk, client.organization_id), client.id, **data
            )


class ScopedEventAdmin(ReadOnlyAdmin):
    permission = "clients.read"
    list_display = ("action", "occurred_at", "before_version", "after_version")

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .filter(
                organization_id__in=authorized_organization_ids(request.user.pk, self.permission)
            )
        )

    def has_module_permission(self, request):
        return bool(authorized_organization_ids(request.user.pk, self.permission))

    def has_view_permission(self, request, obj=None):
        ids = authorized_organization_ids(request.user.pk, self.permission)
        return bool(ids) if obj is None else obj.organization_id in ids


@admin.register(ClientChangeEvent)
class ClientChangeEventAdmin(ScopedEventAdmin):
    pass


@admin.register(ContactChangeEvent)
class ContactChangeEventAdmin(ScopedEventAdmin):
    permission = "contacts.read"
