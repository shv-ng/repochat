from rest_framework_simplejwt.authentication import JWTAuthentication
import logging
import json
import uuid

from django.http import StreamingHttpResponse
from langchain_core.messages import AIMessage, HumanMessage
from django.http.response import JsonResponse
from django.views import View

from apps.chat.models import ChatMessage, ChatSession
from apps.repos.models import Repo
from services.llm.stream import stream_answer
from services.vectorstore.chroma import Embed

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator


# Create your views here.
class ChatHistoryView(View):
    def get(self, request):
        session_id = request.GET.get("session_id")
        if not session_id:
            return JsonResponse({"error": "session_id required"}, status=400)
        
        messages = ChatMessage.objects.filter(session__session_id=session_id).order_by("created_at")[:50]
        data = [{"role": m.role, "content": m.content} for m in messages]
        return JsonResponse(data, safe=False)

@method_decorator(csrf_exempt, name="dispatch")
class ChatView(View):
    def get(self, request):
        auth = JWTAuthentication()
        try:
            result = auth.authenticate(request)
            user = result[0] if result else None
        except Exception as e:
            logging.error(e)
            user = None

        repo_url = request.GET.get("repo_url")
        query = request.GET.get("query")
        session_id = request.GET.get("session_id")

        if not repo_url or not query:
            return JsonResponse({"error": "repo_url and query required"}, status=400)

        if not session_id:
            session_id = str(uuid.uuid4())

        try:
            repo = Repo.objects.get(url=repo_url)
        except Repo.DoesNotExist:
            return JsonResponse({"error": "repo not ingested"}, status=400)

        if user:
            session, _ = ChatSession.objects.get_or_create(
                repo=repo, user=user, defaults={"session_id": session_id}
            )
        else:
            session, _ = ChatSession.objects.get_or_create(
                repo=repo, session_id=session_id, defaults={"repo": repo, "user": user}
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
                    yield f"data: {json.dumps({'message': token})}\n\n"
            ChatMessage.objects.create(
                session=session, role=ChatMessage.Role.USER, content=query
            )
            ChatMessage.objects.create(
                session=session, role=ChatMessage.Role.AI, content=full_response
            )

        return StreamingHttpResponse(event_stream(), content_type="text/event-stream")
