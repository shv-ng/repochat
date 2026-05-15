from django.urls import path

from . import views

urlpatterns = [
    path("ingest/", views.IngestionView.as_view(), name="ingest"),
]
