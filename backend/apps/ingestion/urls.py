from django.urls import path
from . import views

urlpatterns = [
    path("ingest/<int:job_id>/", views.IngestionView.as_view(), name="ingest"),
]
