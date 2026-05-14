import celery

app = celery.Celery("tasks", broker="redis://localhost:6379/0")


@app.task(bind=True)
def add(x, y):
    return x + y
