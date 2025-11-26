"""Monitor configuration endpoints (Reddit, LinkedIn, Blog)"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List
from app.models import (
    SubredditMonitorCreate,
    SubredditMonitorResponse,
    BlogMonitorCreate,
    BlogMonitorResponse,
)
from app.auth import get_current_active_user, User
from app.database import get_db
import uuid

router = APIRouter()


# Reddit (Subreddit) Monitors
@router.get("/reddit", response_model=List[SubredditMonitorResponse])
async def list_subreddit_monitors(
    active: bool = Query(True),
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db),
):
    """List all subreddit monitors"""
    query = """
        SELECT id, organization_id, subreddit, engagement_threshold,
               auto_reply, persona_id, check_frequency, last_checked,
               active, created_at
        FROM subreddit_monitors
        WHERE organization_id = $1
    """
    params = [current_user.organization_id]

    if active is not None:
        query += " AND active = $2"
        params.append(active)

    query += " ORDER BY created_at DESC"

    rows = await db.fetch(query, *params)
    return [SubredditMonitorResponse(**dict(row)) for row in rows]


@router.post("/reddit", response_model=SubredditMonitorResponse, status_code=201)
async def create_subreddit_monitor(
    monitor_data: SubredditMonitorCreate,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db),
):
    """Create a new subreddit monitor"""
    # Create monitor
    monitor_id = await db.fetchval(
        """
        INSERT INTO subreddit_monitors (
            organization_id, subreddit, engagement_threshold,
            auto_reply, persona_id
        )
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id
        """,
        current_user.organization_id,
        monitor_data.subreddit,
        monitor_data.engagement_threshold,
        monitor_data.auto_reply,
        monitor_data.persona_id,
    )

    # Link keywords
    if monitor_data.keyword_ids:
        for keyword_id in monitor_data.keyword_ids:
            await db.execute(
                "INSERT INTO subreddit_keywords (subreddit_monitor_id, keyword_id) VALUES ($1, $2)",
                monitor_id,
                keyword_id,
            )

    row = await db.fetchrow(
        "SELECT * FROM subreddit_monitors WHERE id = $1", monitor_id
    )
    return SubredditMonitorResponse(**dict(row))


@router.get("/reddit/{monitor_id}", response_model=SubredditMonitorResponse)
async def get_subreddit_monitor(
    monitor_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db),
):
    """Get a specific subreddit monitor"""
    row = await db.fetchrow(
        "SELECT * FROM subreddit_monitors WHERE id = $1 AND organization_id = $2",
        monitor_id,
        current_user.organization_id,
    )

    if not row:
        raise HTTPException(status_code=404, detail="Monitor not found")

    return SubredditMonitorResponse(**dict(row))


@router.delete("/reddit/{monitor_id}", status_code=204)
async def delete_subreddit_monitor(
    monitor_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db),
):
    """Delete a subreddit monitor"""
    result = await db.execute(
        "DELETE FROM subreddit_monitors WHERE id = $1 AND organization_id = $2",
        monitor_id,
        current_user.organization_id,
    )

    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Monitor not found")

    return None


# Blog Monitors
@router.get("/blogs", response_model=List[BlogMonitorResponse])
async def list_blog_monitors(
    active: bool = Query(True),
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db),
):
    """List all blog monitors"""
    query = """
        SELECT id, organization_id, blog_url, blog_name, rss_feed,
               check_frequency, last_checked, active, created_at
        FROM blog_monitors
        WHERE organization_id = $1
    """
    params = [current_user.organization_id]

    if active is not None:
        query += " AND active = $2"
        params.append(active)

    query += " ORDER BY created_at DESC"

    rows = await db.fetch(query, *params)
    return [BlogMonitorResponse(**dict(row)) for row in rows]


@router.post("/blogs", response_model=BlogMonitorResponse, status_code=201)
async def create_blog_monitor(
    monitor_data: BlogMonitorCreate,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db),
):
    """Create a new blog monitor"""
    # Check tier limits
    count = await db.fetchval(
        "SELECT COUNT(*) FROM blog_monitors WHERE organization_id = $1 AND active = true",
        current_user.organization_id,
    )

    limits = {"starter": 0, "growth": 15, "enterprise": 999}
    if count >= limits.get(current_user.tier, 0):
        raise HTTPException(
            status_code=403,
            detail=f"Blog monitor limit reached for {current_user.tier} tier",
        )

    monitor_id = await db.fetchval(
        """
        INSERT INTO blog_monitors (
            organization_id, blog_url, blog_name, rss_feed, check_frequency
        )
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id
        """,
        current_user.organization_id,
        monitor_data.blog_url,
        monitor_data.blog_name,
        monitor_data.rss_feed,
        monitor_data.check_frequency,
    )

    row = await db.fetchrow("SELECT * FROM blog_monitors WHERE id = $1", monitor_id)
    return BlogMonitorResponse(**dict(row))


@router.delete("/blogs/{monitor_id}", status_code=204)
async def delete_blog_monitor(
    monitor_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db),
):
    """Delete a blog monitor"""
    result = await db.execute(
        "DELETE FROM blog_monitors WHERE id = $1 AND organization_id = $2",
        monitor_id,
        current_user.organization_id,
    )

    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Monitor not found")

    return None
