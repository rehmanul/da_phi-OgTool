"""Detected posts and responses endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from typing import List
from app.models import (
    DetectedPostResponse,
    GenerateResponseRequest,
    GeneratedResponseResponse,
    ApproveResponseRequest,
)
from app.auth import get_current_active_user, User
from app.database import get_db
import uuid
import json

router = APIRouter()


@router.get("", response_model=List[DetectedPostResponse])
async def list_posts(
    platform: str = Query(None),
    status: str = Query(None),
    priority: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db),
):
    """List detected posts"""
    offset = (page - 1) * page_size

    query = """
        SELECT id, organization_id, platform, external_id, url, parent_url,
               title, content, author, author_profile_url, subreddit,
               engagement_score, comment_count, relevance_score, sentiment_score,
               keyword_matches, metadata, priority, status, detected_at
        FROM detected_posts
        WHERE organization_id = $1
    """
    params = [current_user.organization_id]

    if platform:
        query += f" AND platform = ${len(params) + 1}"
        params.append(platform)

    if status:
        query += f" AND status = ${len(params) + 1}"
        params.append(status)

    if priority:
        query += f" AND priority = ${len(params) + 1}"
        params.append(priority)

    query += f" ORDER BY detected_at DESC LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}"
    params.extend([page_size, offset])

    rows = await db.fetch(query, *params)

    return [DetectedPostResponse(**dict(row)) for row in rows]


@router.get("/{post_id}", response_model=DetectedPostResponse)
async def get_post(
    post_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db),
):
    """Get a specific post"""
    row = await db.fetchrow(
        "SELECT * FROM detected_posts WHERE id = $1 AND organization_id = $2",
        post_id,
        current_user.organization_id,
    )

    if not row:
        raise HTTPException(status_code=404, detail="Post not found")

    return DetectedPostResponse(**dict(row))


@router.post("/{post_id}/generate", response_model=GeneratedResponseResponse, status_code=202)
async def generate_response(
    post_id: uuid.UUID,
    request_data: GenerateResponseRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db),
):
    """Generate AI response for a post"""
    # Verify post exists
    post = await db.fetchrow(
        "SELECT id FROM detected_posts WHERE id = $1 AND organization_id = $2",
        post_id,
        current_user.organization_id,
    )

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # Check if response already exists
    existing = await db.fetchrow(
        "SELECT * FROM generated_responses WHERE post_id = $1 ORDER BY created_at DESC LIMIT 1",
        post_id,
    )

    if existing:
        return GeneratedResponseResponse(**dict(existing))

    # Publish to message queue for processing
    from aio_pika import connect_robust, Message
    from app.config import settings

    connection = await connect_robust(settings.RABBITMQ_URL)
    channel = await connection.channel()
    exchange = await channel.get_exchange("ogtool")

    message_body = {
        "post_id": str(post_id),
        "organization_id": str(current_user.organization_id),
        "persona_id": str(request_data.persona_id) if request_data.persona_id else None,
        "platform": post["platform"],
        "auto_reply": False,
    }

    await exchange.publish(
        Message(body=json.dumps(message_body).encode()),
        routing_key="post.detected",
    )

    await channel.close()
    await connection.close()

    return {"message": "Response generation queued", "post_id": str(post_id)}


@router.get("/{post_id}/responses", response_model=List[GeneratedResponseResponse])
async def list_post_responses(
    post_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db),
):
    """List all generated responses for a post"""
    rows = await db.fetch(
        """
        SELECT gr.id, gr.post_id, gr.persona_id, gr.response_text,
               gr.quality_score, gr.safety_score, gr.approved, gr.posted,
               gr.created_at
        FROM generated_responses gr
        JOIN detected_posts dp ON gr.post_id = dp.id
        WHERE dp.id = $1 AND dp.organization_id = $2
        ORDER BY gr.created_at DESC
        """,
        post_id,
        current_user.organization_id,
    )

    return [GeneratedResponseResponse(**dict(row)) for row in rows]


@router.post("/{post_id}/responses/{response_id}/approve")
async def approve_response(
    post_id: uuid.UUID,
    response_id: uuid.UUID,
    approval_data: ApproveResponseRequest,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db),
):
    """Approve or reject a generated response"""
    # Verify ownership
    response = await db.fetchrow(
        """
        SELECT gr.id
        FROM generated_responses gr
        JOIN detected_posts dp ON gr.post_id = dp.id
        WHERE gr.id = $1 AND dp.organization_id = $2
        """,
        response_id,
        current_user.organization_id,
    )

    if not response:
        raise HTTPException(status_code=404, detail="Response not found")

    # Update approval status
    await db.execute(
        """
        UPDATE generated_responses
        SET approved = $1, approved_by = $2, approved_at = NOW()
        WHERE id = $3
        """,
        approval_data.approved,
        current_user.id,
        response_id,
    )

    return {"message": "Response approval status updated"}


@router.post("/{post_id}/responses/{response_id}/post")
async def post_response(
    post_id: uuid.UUID,
    response_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db),
):
    """Post an approved response to the platform"""
    # Verify response is approved
    response = await db.fetchrow(
        """
        SELECT gr.id, gr.approved, gr.posted, dp.platform, dp.external_id
        FROM generated_responses gr
        JOIN detected_posts dp ON gr.post_id = dp.id
        WHERE gr.id = $1 AND dp.organization_id = $2
        """,
        response_id,
        current_user.organization_id,
    )

    if not response:
        raise HTTPException(status_code=404, detail="Response not found")

    if not response["approved"]:
        raise HTTPException(status_code=400, detail="Response not approved")

    if response["posted"]:
        raise HTTPException(status_code=400, detail="Response already posted")

    # Mark as posted (actual posting would be done by background worker)
    await db.execute(
        """
        UPDATE generated_responses
        SET posted = true, posted_at = NOW(), posted_by = $1
        WHERE id = $2
        """,
        current_user.id,
        response_id,
    )

    # Update post status
    await db.execute(
        "UPDATE detected_posts SET status = 'responded' WHERE id = $1",
        post_id,
    )

    return {"message": "Response posted successfully"}
