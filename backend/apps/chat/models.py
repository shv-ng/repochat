import uuid

from django.db import models

from apps.repos.models import Repo

# Create your models here.


class ChatSession(models.Model):
    session_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    repo = models.ForeignKey(
        Repo, on_delete=models.CASCADE, related_name="chat_sessions"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.repo.url} - {self.session_id}"


class ChatMessage(models.Model):
    class Role(models.TextChoices):
        USER = "user"
        AI = "ai"

    session = models.ForeignKey(
        ChatSession, on_delete=models.CASCADE, related_name="messages"
    )
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.USER)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.session.repo.url} - {self.session.session_id} - {self.content}"
