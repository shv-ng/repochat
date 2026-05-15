import json
from time import sleep

from django.http import StreamingHttpResponse
from django.http.response import JsonResponse

from django.views import View
from apps.ingestion.models import IngestionJob
from tasks.ingest import ingest_repo


from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator


# Create your views here.
@method_decorator(csrf_exempt, name="dispatch")
class IngestionView(View):
    def get(self, request):
        job_id = request.GET.get("job_id")
        if not job_id:
            return JsonResponse({"error": "job_id required"}, status=400)

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

    def post(self, request):
        data = json.loads(request.body)
        repo_url = data.get("repo_url")
        if not repo_url:
            return JsonResponse({"error": "repo_url required"}, status=400)

        job = IngestionJob.objects.create(repo_url=repo_url)
        ingest_repo.delay(job.id, repo_url)

        return JsonResponse({"job_id": job.id})
