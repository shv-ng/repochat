from rest_framework import generics
from django.contrib.auth.models import User
from .serializers import UserSerializer

# Create your views here.


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = []
    authentication_classes = []
