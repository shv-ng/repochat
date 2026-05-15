from rest_framework import serializers

from .models import Repo


class RepoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Repo
        fields = ["id", "url", "collection_name"]
        extra_kwargs = {"collection_name": {"write_only": True}}
