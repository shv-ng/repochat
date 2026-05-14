import asyncio
import uuid

import tasks
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
async def ingest(github_url: str, background_tasks: BackgroundTasks):
    """Ingest endpoint
    Args:
        github_url (str): github url
    """
    task_id = str(uuid.uuid4())[:8]
    background_tasks.add_task(tasks.background_ingest, task_id, github_url)

    return {"task_id": task_id}


@app.get("/status", response_class=EventSourceResponse)
async def get_ingest_status(task_id: str):
    while True:
        status = tasks.ingest_status(task_id)
        yield {"data": {"task_id": task_id, "status": status}}
        await asyncio.sleep(0.2)
        if status == "done" or status.startswith("error"):
            break
    yield {"data": {"task_id": task_id, "status": status}}
