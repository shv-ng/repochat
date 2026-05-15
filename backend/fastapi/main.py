import asyncio
import uuid

from auth.router import router as auth_router
from dotenv import load_dotenv
from embed import Embed
from fastapi import BackgroundTasks, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.sse import EventSourceResponse
from langchain_core.messages import AIMessage, HumanMessage
from llm import stream_answer
from tasks import background_ingest, ingest_status

load_dotenv()


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)


@app.get("/")
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


@app.get("/chat", response_class=EventSourceResponse)
async def chat(repo_url: str, question: str, session_id: str = "default"):
    """Chat endpoint
    Args:
        repo_url (str): github url
        question (str): question
        session_id (str): session id

    """
    results = Embed(repo_url).query(question)
    history = chat_history.get(session_id, [])
    if len(history) > 10:
        history = history[-10:]

    full_response = ""

    for token in stream_answer(repo_url, question, results, history):
        if token:
            full_response += token
            yield {"data": token}

    chat_history.setdefault(session_id, [])
    chat_history[session_id].extend(
        [HumanMessage(content=question), AIMessage(content=full_response)]
    )
    yield {"data": full_response}
