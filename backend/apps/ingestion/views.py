import json
from time import sleep

from django.http import StreamingHttpResponse
from rest_framework.request import Request
from rest_framework.response import Response

from django.views import View
from apps.ingestion.models import IngestionJob
from tasks.ingest import ingest_repo


class IngestionView(View):
    def get(
        self,
        request: Request,
    ):
        job_id = request.query_params.get("job_id")
        if not job_id:
            return Response({"error": "job_id required"}, status=400)

        def event_stream():
            last_message = None

            while True:
                try:
                    job = IngestionJob.objects.get(id=job_id)
                except IngestionJob.DoesNotExist:
                    yield f"data: {json.dumps({'status': 'error', 'message': 'Job not found'})}\n\n"
                    break

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

                if job.status in [
                    IngestionJob.Status.COMPLETED,
                    IngestionJob.Status.ERROR,
                ]:
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

        return Response({"job_id": job.id})
