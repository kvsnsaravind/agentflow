from celery_app import celery_app
from agents.orchestrator import AgentOrchestrator

# Initialize orchestrator once when worker starts
orchestrator = AgentOrchestrator()


@celery_app.task(bind=True, name="run_agentflow")
def run_agentflow_task(self, task: str) -> dict:
    """
    Celery background task that runs the full AgentFlow pipeline.

    This is what makes the API non-blocking:
    - FastAPI receives request → pushes this task to Redis queue → returns job_id instantly
    - This worker picks up the task from Redis queue and processes it
    - Result is stored back in Redis when complete
    - User polls /status/{job_id} to check if done

    The 'bind=True' gives access to 'self' which lets us
    update task state (STARTED, PROGRESS, SUCCESS, FAILURE)
    so the frontend can track progress in real-time.
    """
    try:
        # Update task state to STARTED
        self.update_state(
            state="STARTED",
            meta={"status": "AgentFlow pipeline started", "current_agent": "Planner"}
        )

        # Run the full agent pipeline
        result = orchestrator.run(task)

        # Return result — Celery stores this in Redis automatically
        return result

    except Exception as e:
        # Update task state to FAILURE
        self.update_state(
            state="FAILURE",
            meta={"error": str(e)}
        )
        raise e