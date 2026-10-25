from django.urls import path

from .views import (
    ProjectAccessEndView,
    ProjectAccessOptionsView,
    ProjectAccessView,
    ProjectOptionsView,
    ProjectsView,
    ProjectTransitionView,
    ProjectView,
)
from .workforce import WorkforceEndView, WorkforceOptionsView, WorkforceView

urlpatterns = [
    path("<uuid:org>/projects/<uuid:project>/workforce/", WorkforceView.as_view()),
    path("<uuid:org>/projects/<uuid:project>/workforce/options/", WorkforceOptionsView.as_view()),
    path(
        "<uuid:org>/projects/<uuid:project>/workforce/<uuid:worker>/end/",
        WorkforceEndView.as_view(),
    ),
    path("<uuid:org>/projects/", ProjectsView.as_view()),
    path("<uuid:org>/projects/options/", ProjectOptionsView.as_view()),
    path("<uuid:org>/projects/<uuid:project>/", ProjectView.as_view()),
    path("<uuid:org>/projects/<uuid:project>/transition/", ProjectTransitionView.as_view()),
    path("<uuid:org>/projects/<uuid:project>/access/", ProjectAccessView.as_view()),
    path(
        "<uuid:org>/projects/<uuid:project>/access/<uuid:grant>/end/",
        ProjectAccessEndView.as_view(),
    ),
    path("<uuid:org>/projects/<uuid:project>/options/", ProjectAccessOptionsView.as_view()),
]
