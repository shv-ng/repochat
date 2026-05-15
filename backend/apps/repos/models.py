from django.db import models

# Create your models here.


class Repo(models.Model):
    url = models.URLField(unique=True)
    collection_name = models.CharField(max_length=255)
    ingested_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.url
