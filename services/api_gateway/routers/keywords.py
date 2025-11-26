"""Keyword management endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List
from app.models import KeywordCreate, KeywordUpdate, KeywordResponse, PaginatedResponse
from app.auth import get_current_active_user, User
from app.database import get_db
import uuid

router = APIRouter()


@router.get("", response_model=List[KeywordResponse])
async def list_keywords(
    platform: str = Query(None),
    active: bool = Query(True),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db),
):
    """List all keywords for the organization"""
    offset = (page - 1) * page_size

    query = """
        SELECT id, organization_id, keyword, platform, filters, priority,
               alert_threshold, active, created_at, updated_at
        FROM keywords
        WHERE organization_id = $1
    """
    params = [current_user.organization_id]

    if platform:
        query += f" AND platform = ${len(params) + 1}"
        params.append(platform)

    if active is not None:
        query += f" AND active = ${len(params) + 1}"
        params.append(active)

    query += f" ORDER BY created_at DESC LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}"
    params.extend([page_size, offset])

    rows = await db.fetch(query, *params)

    return [KeywordResponse(**dict(row)) for row in rows]


@router.post("", response_model=KeywordResponse, status_code=201)
async def create_keyword(
    keyword_data: KeywordCreate,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db),
):
    """Create a new keyword"""
    # Check tier limits
    count = await db.fetchval(
        "SELECT COUNT(*) FROM keywords WHERE organization_id = $1 AND platform = $2 AND active = true",
        current_user.organization_id,
        keyword_data.platform,
    )

    limits = {"starter": 10, "growth": 30, "enterprise": 999999}
    if count >= limits.get(current_user.tier, 10):
        raise HTTPException(
            status_code=403,
            detail=f"Keyword limit reached for {current_user.tier} tier",
        )

    keyword_id = await db.fetchval(
        """
        INSERT INTO keywords (organization_id, keyword, platform, filters, priority)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id
        """,
        current_user.organization_id,
        keyword_data.keyword,
        keyword_data.platform,
        keyword_data.filters,
        keyword_data.priority,
    )

    row = await db.fetchrow("SELECT * FROM keywords WHERE id = $1", keyword_id)
    return KeywordResponse(**dict(row))


@router.get("/{keyword_id}", response_model=KeywordResponse)
async def get_keyword(
    keyword_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db),
):
    """Get a specific keyword"""
    row = await db.fetchrow(
        "SELECT * FROM keywords WHERE id = $1 AND organization_id = $2",
        keyword_id,
        current_user.organization_id,
    )

    if not row:
        raise HTTPException(status_code=404, detail="Keyword not found")

    return KeywordResponse(**dict(row))


@router.put("/{keyword_id}", response_model=KeywordResponse)
async def update_keyword(
    keyword_id: uuid.UUID,
    keyword_data: KeywordUpdate,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db),
):
    """Update a keyword"""
    # Check exists
    existing = await db.fetchval(
        "SELECT id FROM keywords WHERE id = $1 AND organization_id = $2",
        keyword_id,
        current_user.organization_id,
    )

    if not existing:
        raise HTTPException(status_code=404, detail="Keyword not found")

    # Build update query
    update_fields = []
    params = []
    param_count = 1

    for field, value in keyword_data.dict(exclude_unset=True).items():
        update_fields.append(f"{field} = ${param_count}")
        params.append(value)
        param_count += 1

    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    params.append(keyword_id)
    query = f"UPDATE keywords SET {', '.join(update_fields)} WHERE id = ${param_count} RETURNING *"

    row = await db.fetchrow(query, *params)
    return KeywordResponse(**dict(row))


@router.delete("/{keyword_id}", status_code=204)
async def delete_keyword(
    keyword_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db),
):
    """Delete a keyword"""
    result = await db.execute(
        "DELETE FROM keywords WHERE id = $1 AND organization_id = $2",
        keyword_id,
        current_user.organization_id,
    )

    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Keyword not found")

    return None
