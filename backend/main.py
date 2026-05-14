import uuid

from dotenv import load_dotenv
from fastapi import FastAPI, BackgroundTasks

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
    background_tasks.add_task(background_ingest, task_id, github_url)

    return {"task_id": task_id}
