from rest_framework.views import APIView
from rest_framework.request import Request
from apps.ingestion.models import IngestionJob
from rest_framework.response import Response
from tasks.ingest import ingest_repo


class IngestionView(APIView):
    def get(self, request: Request):
        return Response("Ingestion")

    def post(self, request: Request):
        repo_url = request.POST.get("repo_url")
        if not repo_url:
            return Response({"error": "repo_url required"}, status=400)

        job = IngestionJob.objects.create(repo_url=repo_url)
        ingest_repo.delay(job.id, repo_url)

        return Response({"task_id": job.id})
