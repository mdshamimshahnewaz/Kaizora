from django.urls import path

from .access_views import (
    AssignmentsView,
    CatalogView,
    PermissionsView,
    RevokeView,
    RolesView,
    RoleView,
)

urlpatterns = [
    path("<uuid:org>/permissions/me/", PermissionsView.as_view()),
    path("<uuid:org>/permissions/catalog/", CatalogView.as_view()),
    path("<uuid:org>/roles/", RolesView.as_view()),
    path("<uuid:org>/roles/<uuid:role>/", RoleView.as_view()),
    path("<uuid:org>/role-assignments/", AssignmentsView.as_view()),
    path("<uuid:org>/role-assignments/<uuid:assignment>/revoke/", RevokeView.as_view()),
]
