from celery import Celery

# ── Celery Configuration ───────────────────────────────────────────────────
# Redis runs on port 6380 (our custom port)
# broker = Redis acts as message queue (holds tasks)
# backend = Redis acts as result store (holds completed results)

celery_app = Celery(
    "agentflow",
    broker="redis://localhost:6380/0",    # Redis as task queue
    backend="redis://localhost:6380/0",   # Redis as result store
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,              # Track when task starts
    result_expires=3600,                  # Results expire after 1 hour
)