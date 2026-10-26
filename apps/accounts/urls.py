from django.urls import path
from .views import AccountsIndexView

urlpatterns = [
    path("", AccountsIndexView.as_view(), name="accounts-index"),
]
