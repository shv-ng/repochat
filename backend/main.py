import asyncio
import inspect
from embed import Embed
import uuid

from langchain_core.messages import AIMessage, HumanMessage
from llm import stream_answer
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
    task_id = str(uuid.uuid4())[:8]
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
    print("break here")
    results = Embed(repo_url).query(question)
    print("break here")
    history = chat_history.get(session_id, [])

    print("break here")
    full_response = ""

    print("break here")

    async def event_stream():
        print("break here")
        nonlocal full_response
        print("break here")
        async for token in stream_answer(repo_url, question, results, history):
            print("break here")
            if token:
                print("break here")
                full_response += token
                print("break here")
                yield {"data": token}

        print("break here")
        chat_history.setdefault(session_id, [])
        print("break here")
        chat_history[session_id].extend(
            [HumanMessage(content=question), AIMessage(content=full_response)]
        )
        print("break here")

    print("break here")
    print(inspect.isasyncgen(event_stream()))
    return EventSourceResponse(event_stream())
