from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from celery_app import celery_app
from worker import run_agentflow_task

app = FastAPI(title="AgentFlow API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TaskRequest(BaseModel):
    task: str


@app.get("/")
def root():
    return {"message": "AgentFlow API v2.0 with Redis Queue is running! 🚀"}


@app.post("/run")
def run_agents(request: TaskRequest):
    """
    NEW BEHAVIOR with Redis:
    - Before: blocks for 40 seconds, then returns result
    - After:  returns job_id in 1ms, worker processes in background

    Flow:
    1. Receives task
    2. Pushes to Redis queue via Celery
    3. Returns job_id INSTANTLY
    4. Worker picks up task and processes it
    5. Frontend polls /status/{job_id} for result
    """
    if not request.task.strip():
        raise HTTPException(status_code=400, detail="Task cannot be empty")

    # Push task to Redis queue — returns immediately!
    job = run_agentflow_task.delay(request.task)

    return {
        "job_id": job.id,
        "status": "queued",
        "message": "Task queued! Poll /status/{job_id} for results"
    }


@app.get("/status/{job_id}")
def get_status(job_id: str):
    """
    Polls Redis for the status of a job.
    Frontend calls this every 2 seconds until status is SUCCESS.

    Possible states:
    - PENDING  → Task is waiting in Redis queue
    - STARTED  → Worker picked it up and is processing
    - SUCCESS  → Done! Result is available
    - FAILURE  → Something went wrong
    """
    job = celery_app.AsyncResult(job_id)

    if job.state == "PENDING":
        return {"job_id": job_id, "status": "pending", "message": "Waiting in queue..."}

    elif job.state == "STARTED":
        return {"job_id": job_id, "status": "started", "message": "AgentFlow is running..."}

    elif job.state == "SUCCESS":
        return {
            "job_id": job_id,
            "status": "success",
            "result": job.result
        }

    elif job.state == "FAILURE":
        return {
            "job_id": job_id,
            "status": "failure",
            "error": str(job.result)
        }

    else:
        return {"job_id": job_id, "status": job.state}


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "queue": "Redis:6380",
        "agents": ["planner", "researcher", "executor", "synthesizer"]
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)