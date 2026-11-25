from django.urls import path
from .views import (LoginView, SucessoView)

urlpatterns = [
    path("", LoginView.as_view(), name="login"),
    path("sucesso/", SucessoView.as_view(), name="sucesso")
]