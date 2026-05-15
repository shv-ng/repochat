from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request
# Create your views here.


class IngestionView(APIView):
    def get(self, request: Request):
        return Response("Ingestion")

    def post(self, request: Request):
        return Response("Ingestion")
