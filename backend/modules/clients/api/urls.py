from django.urls import path

from .views import ClientsView, ClientView, ContactsView, ContactView

urlpatterns = [
    path("<uuid:org>/clients/", ClientsView.as_view()),
    path("<uuid:org>/clients/<uuid:client>/", ClientView.as_view()),
    path("<uuid:org>/clients/<uuid:client>/contacts/", ContactsView.as_view()),
    path("<uuid:org>/clients/<uuid:client>/contacts/<uuid:contact>/", ContactView.as_view()),
]
