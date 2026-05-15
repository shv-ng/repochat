from rest_framework.views import APIView
from rest_framework.response import Response
from apps.chat.models import ChatSession
from apps.repos.models import Repo


# Create your views here.
class ChatView(APIView):
    def get(self, request):
        repo_url = request.query_params.get("repo_url")
        query = request.query_params.get("query")
        session_id = request.query_params.get("session_id", "default")

        if not repo_url or not query:
            return Response({"error": "repo_url and query required"}, status=400)

        try:
            repo = Repo.objects.get(url=repo_url)
        except Repo.DoesNotExist:
            return Response({"error": "repo not ingested"}, status=400)

        session, _ = ChatSession.objects.get_or_create(
            repo=repo, session_id=session_id, defaults={"repo": repo}
        )
        messages = session.messages.order_by("-created_at")[:10]
        [
            {
                "role": message.role,
                "content": message.content,
            }
            for message in messages
        ]

        return Response({"message": "Hello, world!"})
