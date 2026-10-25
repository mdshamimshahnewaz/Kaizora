from django.urls import path

from .account_views import AccountView

urlpatterns = [path("me/", AccountView.as_view(), name="account-me")]
