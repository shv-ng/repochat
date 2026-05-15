import json
from time import sleep

from apps.ingestion.models import IngestionJob
from django.http import StreamingHttpResponse
from django.http.response import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import AccessToken
from tasks.ingest import ingest_repo


# Create your views here.
@method_decorator(csrf_exempt, name="dispatch")
class IngestionView(View):
    def get(self, request):
        job_id = request.GET.get("job_id")
        token = request.GET.get("token")
        if not job_id:
            return JsonResponse({"error": "job_id required"}, status=400)

        # Authenticate
        try:
            if token:
                access_token = AccessToken(token)
                from django.contrib.auth import get_user_model

                User = get_user_model()
                user = User.objects.get(id=access_token["user_id"])
            else:
                auth = JWTAuthentication()
                user_auth = auth.authenticate(request)
                if not user_auth:
                    return JsonResponse({"error": "Unauthorized"}, status=401)
                user = user_auth[0]
        except Exception:
            return JsonResponse({"error": "Unauthorized"}, status=401)

        def event_stream():
            last_message = None

            while True:
                try:
                    job = IngestionJob.objects.get(id=job_id, user=user)
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
        # Authenticate
        auth = JWTAuthentication()
        user_auth = auth.authenticate(request)
        if not user_auth:
            return JsonResponse({"error": "Unauthorized"}, status=401)
        user = user_auth[0]

        data = json.loads(request.body)
        repo_url = data.get("repo_url")
        if not repo_url:
            return JsonResponse({"error": "repo_url required"}, status=400)

        job = IngestionJob.objects.create(repo_url=repo_url, user=user)
        ingest_repo.delay(job.id, repo_url, user.id)

        return JsonResponse({"job_id": job.id})
