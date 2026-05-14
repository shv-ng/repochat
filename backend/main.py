import asyncio
from embed import Embed
from llm import stream_answer
import uuid
from llm import format_context

from langchain_core.messages import AIMessage, HumanMessage
from tasks import background_ingest, ingest_status
from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI
from fastapi.sse import EventSourceResponse

load_dotenv()

app = FastAPI()


@app.get("/health")
def health():
    """Health check endpoint"""
    return {"status": "ok"}


@app.post("/ingest")
async def ingest(repo_url: str, background_tasks: BackgroundTasks):
    """Ingest endpoint
    Args:
        repo_url (str): github url
    """
    task_id = str(uuid.uuid4())[:6]
    background_tasks.add_task(background_ingest, task_id, repo_url)

    return {"task_id": task_id}


@app.get("/status", response_class=EventSourceResponse)
async def get_ingest_status(task_id: str):
    while True:
        status = ingest_status(task_id)
        await asyncio.sleep(0.2)
        if status == "done" or status.startswith("error"):
            break
        yield {"data": {"task_id": task_id, "status": status}}
    yield {"data": {"task_id": task_id, "status": status}}


chat_history = {}


@app.post("/chat", response_class=EventSourceResponse)
async def chat(repo_url: str, question: str, session_id: str = "default"):
    """Chat endpoint
    Args:
        repo_url (str): github url
        question (str): question
        session_id (str): session id

    """
    results = Embed(repo_url).query(question)
    history = chat_history.get(session_id, [])

    full_response = ""
    format_context(results)

    for token in stream_answer(repo_url, question, results, history):
        if token:
            full_response += token
            yield token

    chat_history.setdefault(session_id, [])
    chat_history[session_id].extend(
        [HumanMessage(content=question), AIMessage(content=full_response)]
    )
    yield {"data": full_response}
