import uuid
from pathlib import Path

from clone import CloneRepo
from dotenv import load_dotenv
from embed import Embed
from fastapi import BackgroundTasks, FastAPI
from splitter import chunk_with_metadata

load_dotenv()

app = FastAPI()


ingestion_status = {}


@app.get("/health")
def health():
    return {"status": "ok"}


def background_ingest(task_id: str, github_url: str):
    try:
        ingestion_status[task_id] = "Cloning repository..."
        clone = CloneRepo(github_url)
        clone.clone_repo()

        ingestion_status[task_id] = "Extracting and embedding files..."
        embed = Embed(github_url)

        files = list(clone.get_repo_files())
        total_files = len(files)

        for i, file in enumerate(files):
            if CloneRepo.is_text_file(file):
                content = Path(file).read_text()
                chunks = chunk_with_metadata(file, content)
                for chunk in chunks:
                    embed.embed(chunk.page_content, chunk.metadata)

                ingestion_status[task_id] = f"Processing: {i + 1}/{total_files} files"

        ingestion_status[task_id] = "done"
    except Exception as e:
        ingestion_status[task_id] = f"error: {str(e)}"


@app.post("/ingest")
async def ingest(github_url: str, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())[:8]
    ingestion_status[task_id] = "accepted"

    background_tasks.add_task(background_ingest, task_id, github_url)

    print(ingestion_status)
    return {"task_id": task_id, "status": "processing", "url": f"/status/{task_id}"}


@app.get("/status/{task_id}")
async def get_status(task_id: str):
    status = ingestion_status.get(task_id, "Not found")
    print(ingestion_status)
    return {"task_id": task_id, "status": status}
