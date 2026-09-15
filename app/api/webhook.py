import hmac
import hashlib
import json
import logging
from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException, Header, status
from pydantic import BaseModel
from app.config import settings
from app.workers.tasks import process_pull_request_task

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

def verify_github_signature(secret: str, signature: str, payload: bytes) -> bool:

    """Verify the GitHub webhook signature."""
    if not signature.startswith("sha256="):
        return False
    
    expected_signature = "sha256=" + hmac.new(
        secret.encode(), 
        payload, 
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected_signature, signature)

class WebhookResponse(BaseModel):
    status: str
    message: str
    delivery_id: str | None = None


@router.post(
    "/github"
    status_code=status.HTTP_200_ACCEPTED,
    response_model=WebhookResponse,
    summary="GitHub Webhook Endpoint",
)
async def github_webhook_handler(
    request: Request,
    x_hub_signature_256: str = Header(..., alias="X-Hub-Signature-256"),
    x_github_delivery: str = Header(..., alias="X-GitHub-Delivery"),
    x_github_event: str = Header(..., alias="X-GitHub-Event"),
):
    """Handle GitHub webhook events."""
    payload_bytes = await request.body()

    if not verify_github_signature(
        payload = payload_bytes,
        secret = settings.GITHUB_WEBHOOK_SECRET,
        signature = x_hub_signature_256
    ):
        logger.warning(f"Invalid GitHub signature for delivery ID {x_github_delivery}")
        raise HTTPException(
            status_=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid signature"
        )

    if x_github_event != "pull_request":
        return WebhookResponse(
            status="ignored",
            message=f"Ignored GitHub event '{x_github_event}'",
            delivery_id=x_github_delivery
        )

    try:
        payload: Dict[str, Any] = json.loads(payload_bytes)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload"
        )

    action = payload.get("action")

    if action not in ["opened", "reopened", "synchronize"]:
        return WebhookResponse(
            status="ignored",
            message=f"Ignored pull_request action '{action}'",
            delivery_id=x_github_delivery
        )

    pr_data = payload.get("pull_request", {})
    repo_data = payload.get("repository", {})

    task_payload = {
        "delivery_id": x_github_delivery,
        "repo_full_name": repo_data.get("full_name"),
        "pull_number": pr_data.get("number"),
        "pr_action": action,
        "head_sha": pr_data.get("head", {}).get("sha"),
        "patch_url": pr_data.get("patch_url"),
    }

    process_pull_request_task.delay(task_payload)

    logger.info(
        f"Queued task for pull request review #{pr_data.get('number')} in repository {repo_data.get('full_name')} (delivery ID: {x_github_delivery})"
    )

    return WebhookResponse(
        status="accepted",
        message="Review task queued successfully",
        delivery_id=x_github_delivery
);