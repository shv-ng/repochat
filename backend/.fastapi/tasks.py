import shutil
from pathlib import Path

import redis
from clone import CloneRepo
from embed import Embed
from splitter import chunk_with_metadata

r = redis.Redis(host="localhost", port=6379, decode_responses=True)


def background_ingest(task_id: str, repo_url: str):
    """Background ingest function
    Args:
        task_id (str): task id
        repo_url (str): repo url
    """
    try:
        r.set(task_id, "Cloning repo...")
        clone = CloneRepo(repo_url)
        clone.clone_repo()

        r.set(task_id, "Extracting and embedding files...")
        embed = Embed(repo_url)

        files = list(clone.get_repo_files())
        total_files = len(files)

        for i, file in enumerate(files):
            try:
                if CloneRepo.is_text_file(file):
                    content = Path(file).read_text(encoding="utf-8", errors="ignore")

                    chunks = chunk_with_metadata(file, content)
                    for chunk in chunks:
                        embed.embed(chunk.page_content, chunk.metadata)

                r.set(task_id, f"Processing: {i + 1}/{total_files} files")

            except Exception as file_error:
                print(f"Skipping {file} due to error: {file_error}")
                continue

        r.set(task_id, "done")
    except Exception as e:
        r.set(task_id, f"error: {str(e)}")
    finally:
        shutil.rmtree(clone.repo_path)


def ingest_status(task_id: str):
    return r.get(task_id)
