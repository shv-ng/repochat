from django.urls import path
from . import views


urlpatterns = [
    path("repos/", views.RepoView.as_view(), name="repo"),
]
