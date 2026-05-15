from django.urls import path

from . import views

urlpatterns = [
    path("chat/", views.ChatView.as_view(), name="chat"),
    path("chat/history/", views.ChatHistoryView.as_view(), name="chat_history"),
]
