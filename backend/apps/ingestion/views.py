from rest_framework.views import APIView
from rest_framework.request import Request
from apps.ingestion.models import IngestionJob
from rest_framework.response import Response
from tasks.ingest import ingest_repo

from time import sleep
from django.http import StreamingHttpResponse
import json


class IngestionView(APIView):
    def get(self, request: Request, job_id: int):
        def event_stream():
            last_message = None

            while True:
                job = IngestionJob.objects.get(id=job_id)

                if job.message != last_message:
                    last_message = job.message

                    yield f"data: {
                        json.dumps(
                            {
                                'status': job.status,
                                'message': job.message,
                            }
                        )
                    }\n\n"

                if job.status in ["completed", "error"]:
                    break

                sleep(1)

        return StreamingHttpResponse(
            event_stream(),
            content_type="text/event-stream",
        )

    def post(self, request: Request):
        repo_url = request.data.get("repo_url")
        if not repo_url:
            return Response({"error": "repo_url required"}, status=400)

        job = IngestionJob.objects.create(repo_url=repo_url)
        ingest_repo.delay(job.id, repo_url)

        return Response({"task_id": job.id})
