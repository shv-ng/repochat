from fastapi.sse import EventSourceResponse
import uuid
import asyncio
from pathlib import Path

from clone import CloneRepo
from dotenv import load_dotenv
from embed import Embed
from fastapi import FastAPI
from pydantic import BaseModel
from splitter import chunk_with_metadata

load_dotenv()

app = FastAPI()


class IngestionStatus(BaseModel):
    task_id: str
    status: str


ingestion_status: dict[str, IngestionStatus] = {}


def background_ingest(task_id: str, github_url: str):
    """Background ingest function
    Args:
        task_id (str): task id
        github_url (str): github url
    """
    try:
        ingestion_status[task_id].status = "Cloning repo..."
        clone = CloneRepo(github_url)
        clone.clone_repo()

        ingestion_status[task_id].status = "Extracting and embedding files..."
        embed = Embed(github_url)

        files = list(clone.get_repo_files())
        total_files = len(files)

        for i, file in enumerate(files):
            if CloneRepo.is_text_file(file):
                content = Path(file).read_text()
                chunks = chunk_with_metadata(file, content)
                for chunk in chunks:
                    embed.embed(chunk.page_content, chunk.metadata)

                ingestion_status[
                    task_id
                ].status = f"Processing: {i + 1}/{total_files} files"

        ingestion_status[task_id].status = "done"
    except Exception as e:
        ingestion_status[task_id].status = f"error: {str(e)}"


@app.get("/health")
def health():
    """Health check endpoint"""
    return {"status": "ok"}


@app.post("/ingest", response_class=EventSourceResponse)
async def ingest(github_url: str):
    """Ingest endpoint
    Args:
        github_url (str): github url
    """
    task_id = str(uuid.uuid4())[:8]
    ingestion_status[task_id] = IngestionStatus(task_id=task_id, status="Queued")

    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, background_ingest, task_id, github_url)

    status = ingestion_status[task_id]
    while True:
        yield status
        await asyncio.sleep(0.5)
        if status.status == "done" or status.status.startswith("error"):
            break
    yield status
