from django.conf import settings
from django.db import models

# Create your models here.


class Repo(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True
    )
    url = models.URLField()
    collection_name = models.CharField(max_length=255)
    ingested_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "url")

    def __str__(self):
        return self.url
