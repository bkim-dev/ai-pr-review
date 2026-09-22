import logging
from celery import Celery
from app.config import settings

logger = logging.getLogger(__name__)

celery_app = Celery(
    "pr_reviewer_tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

@celery_app.task(name="process_pull_request_task", bind=True, max_retries=3)
def process_pull_request_task(self, task_payload: dict):
    """
    Background worker function that picks up queued webhooks.
    This is where Gemini analysis and GitHub API calls happen.
    """
    logger.info(f"Worker picked up PR #{task_payload['pull_number']} for {task_payload['repo_full_name']}")
    
    # 1. Fetch patch diff via GitHub API / PyGithub
    # 2. Call Gemini API using google-genai SDK
    # 3. Post structured inline review comments
    
    return {"status": "completed", "delivery_id": task_payload["delivery_id"]}