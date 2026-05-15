from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from .models import Repo
from .serializers import RepoSerializer


# Create your views here.
class RepoView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = RepoSerializer

    def get_queryset(self):
        return Repo.objects.filter(user=self.request.user).order_by("-ingested_at")
