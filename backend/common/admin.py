from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import reverse
from rest_framework.exceptions import APIException


class ReadOnlyAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class CommandAdmin(admin.ModelAdmin):
    actions = None

    def has_delete_permission(self, request, obj=None):
        return False

    def command_view(self, request, object_id=None):
        try:
            return self._command_view(request, object_id)
        except APIException as error:
            raise PermissionDenied from error

    def _command_view(self, request, object_id=None):
        obj = None
        if object_id:
            obj = self.get_object(request, object_id)
            if obj is None:
                raise Http404
            allowed = self.has_change_permission(request, obj)
        else:
            allowed = self.has_add_permission(request)
        if not allowed:
            raise PermissionDenied
        form = self.command_form(request, obj, request.POST if request.method == "POST" else None)
        if request.method == "POST" and form.is_valid():
            try:
                self.execute(request, obj, form.cleaned_data)
            except APIException as error:
                form.add_error(None, str(error.detail))
            else:
                self.message_user(request, "Change saved.", messages.SUCCESS)
                return HttpResponseRedirect(
                    reverse(f"admin:{self.opts.app_label}_{self.opts.model_name}_changelist")
                )
        return TemplateResponse(
            request,
            "admin/domain_command.html",
            {
                **self.admin_site.each_context(request),
                "opts": self.opts,
                "form": form,
                "title": f"Manage {self.opts.verbose_name}"
                if obj
                else f"Add {self.opts.verbose_name}",
                "original": obj,
            },
        )

    def add_view(self, request, form_url="", extra_context=None):
        return self.command_view(request)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        return self.command_view(request, object_id)
