"""Webhook management endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.models import WebhookCreate, WebhookResponse
from app.auth import get_current_active_user, User
from app.database import get_db
import uuid

router = APIRouter()


@router.get("", response_model=List[WebhookResponse])
async def list_webhooks(
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db),
):
    """List all webhooks"""
    rows = await db.fetch(
        """
        SELECT id, organization_id, name, url, events, active,
               last_triggered, failure_count, created_at
        FROM webhooks
        WHERE organization_id = $1
        ORDER BY created_at DESC
        """,
        current_user.organization_id,
    )

    return [WebhookResponse(**dict(row)) for row in rows]


@router.post("", response_model=WebhookResponse, status_code=201)
async def create_webhook(
    webhook_data: WebhookCreate,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db),
):
    """Create a new webhook"""
    webhook_id = await db.fetchval(
        """
        INSERT INTO webhooks (organization_id, name, url, events, secret)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id
        """,
        current_user.organization_id,
        webhook_data.name,
        webhook_data.url,
        webhook_data.events,
        webhook_data.secret,
    )

    row = await db.fetchrow("SELECT * FROM webhooks WHERE id = $1", webhook_id)
    return WebhookResponse(**dict(row))


@router.get("/{webhook_id}", response_model=WebhookResponse)
async def get_webhook(
    webhook_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db),
):
    """Get a specific webhook"""
    row = await db.fetchrow(
        "SELECT * FROM webhooks WHERE id = $1 AND organization_id = $2",
        webhook_id,
        current_user.organization_id,
    )

    if not row:
        raise HTTPException(status_code=404, detail="Webhook not found")

    return WebhookResponse(**dict(row))


@router.put("/{webhook_id}/toggle")
async def toggle_webhook(
    webhook_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db),
):
    """Toggle webhook active status"""
    webhook = await db.fetchrow(
        "SELECT active FROM webhooks WHERE id = $1 AND organization_id = $2",
        webhook_id,
        current_user.organization_id,
    )

    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    new_status = not webhook["active"]
    await db.execute(
        "UPDATE webhooks SET active = $1 WHERE id = $2",
        new_status,
        webhook_id,
    )

    return {"active": new_status}


@router.delete("/{webhook_id}", status_code=204)
async def delete_webhook(
    webhook_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db),
):
    """Delete a webhook"""
    result = await db.execute(
        "DELETE FROM webhooks WHERE id = $1 AND organization_id = $2",
        webhook_id,
        current_user.organization_id,
    )

    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Webhook not found")

    return None


@router.post("/{webhook_id}/test")
async def test_webhook(
    webhook_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db),
):
    """Test webhook by sending a test payload"""
    webhook = await db.fetchrow(
        "SELECT url, events FROM webhooks WHERE id = $1 AND organization_id = $2",
        webhook_id,
        current_user.organization_id,
    )

    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    # Send test payload
    import httpx
    import json
    from datetime import datetime

    test_payload = {
        "event": "webhook.test",
        "timestamp": datetime.utcnow().isoformat(),
        "data": {
            "message": "This is a test webhook",
            "organization_id": str(current_user.organization_id),
        },
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                webhook["url"],
                json=test_payload,
                headers={"Content-Type": "application/json"},
                timeout=10,
            )

            return {
                "success": response.status_code == 200,
                "status_code": response.status_code,
                "response": response.text[:200],
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }
