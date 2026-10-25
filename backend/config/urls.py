from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/organizations/", include("modules.organizations.api.urls")),
    path("api/v1/organizations/", include("modules.identity.api.access_urls")),
    path("api/v1/organizations/", include("modules.clients.api.urls")),
    path("api/v1/organizations/", include("modules.resources.api.urls")),
    path("api/v1/organizations/", include("modules.projects.api.urls")),
    path("api/v1/auth/", include("modules.identity.api.urls")),
    path("api/v1/account/", include("modules.identity.api.account_urls")),
    path("api/v1/", include("modules.system.api.urls")),
]
if settings.DEBUG:
    urlpatterns += [
        path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
        path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="api-docs"),
    ]
