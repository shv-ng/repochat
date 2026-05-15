import json
import uuid

from django.http import StreamingHttpResponse
from langchain.messages import AIMessage, HumanMessage
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.chat.models import ChatMessage, ChatSession
from apps.repos.models import Repo
from services.llm.stream import stream_answer
from services.vectorstore.chroma import Embed

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator


# Create your views here.
@method_decorator(csrf_exempt, name="dispatch")
class ChatView(APIView):
    def get(self, request):
        repo_url = request.query_params.get("repo_url")
        query = request.query_params.get("query")
        session_id = request.query_params.get("session_id")
        print(repo_url, query, session_id)

        if not repo_url or not query:
            return Response({"error": "repo_url and query required"}, status=400)

        if not session_id:
            session_id = str(uuid.uuid4())

        try:
            repo = Repo.objects.get(url=repo_url)
        except Repo.DoesNotExist:
            return Response({"error": "repo not ingested"}, status=400)

        session, _ = ChatSession.objects.get_or_create(
            repo=repo, session_id=session_id, defaults={"repo": repo}
        )
        messages = session.messages.order_by("-created_at")[:10]
        history = [
            HumanMessage(content=message.content)
            if message.role == "user"
            else AIMessage(content=message.content)
            for message in messages
        ]

        results = Embed(repo_url).query(query)

        def event_stream():
            full_response = ""
            for token in stream_answer(repo_url, query, results, history):
                if token:
                    full_response += token
                    yield f"data: {json.dumps({'message': full_response})}\n\n"
            ChatMessage.objects.create(
                session=session, role=ChatMessage.Role.USER, content=query
            )
            ChatMessage.objects.create(
                session=session, role=ChatMessage.Role.AI, content=full_response
            )

        return StreamingHttpResponse(event_stream(), content_type="text/event-stream")
