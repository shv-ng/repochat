import shutil
from pathlib import Path

from celery import shared_task

from apps.ingestion.models import IngestionJob
from apps.repos.models import Repo
from services.github.clone import CloneRepo
from services.github.parser import chunk_with_metadata
from services.vectorstore.chroma import Embed


@shared_task
def ingest_repo(job_id: int, repo_url: str):
    job = IngestionJob.objects.get(id=job_id)

    try:
        job.status = IngestionJob.Status.RUNNING
        job.message = "Cloning repo..."
        job.save()

        clone = CloneRepo(repo_url)
        clone.clone_repo()

        files = list(clone.get_repo_files())
        total = len(files)
        embed = Embed(repo_url)

        for i, file in enumerate(files):
            try:
                if CloneRepo.is_text_file(file):
                    content = Path(file).read_text(encoding="utf-8", errors="ignore")
                    for chunk in chunk_with_metadata(file, content):
                        embed.embed(chunk.page_content, chunk.metadata)
            except Exception as e:
                print(f"Error processing file: {file} error: {str(e)}")
                continue

            job.message = f"Processing: {i + 1}/{total} files"
            job.save()

        job.status = IngestionJob.Status.COMPLETED
        job.message = "Done"
        job.save()

        Repo.objects.get_or_create(
            url=repo_url, defaults={"collection_name": embed.collection_name}
        )

    except Exception as e:
        job.status = IngestionJob.Status.ERROR
        job.message = str(e)
        job.save()

    finally:
        if clone and getattr(clone, "repo_path", None):
            shutil.rmtree(clone.repo_path, ignore_errors=True)
