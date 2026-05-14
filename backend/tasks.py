import redis

r = redis.Redis(host="localhost", port=6379, decode_responses=True)


def background_ingest(task_id: str, github_url: str):
    """Background ingest function
    Args:
        task_id (str): task id
        github_url (str): github url
    """
    try:
        r.set(task_id, "Cloning repo...")
        clone = CloneRepo(github_url)
        clone.clone_repo()

        r.set(task_id, "Extracting and embedding files...")
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
