from rest_framework.generics import ListAPIView
from .models import Repo
from .serializers import RepoSerializer


# Create your views here.
class RepoView(ListAPIView):
    queryset = Repo.objects.all().order_by("-ingested_at")
    serializer_class = RepoSerializer
