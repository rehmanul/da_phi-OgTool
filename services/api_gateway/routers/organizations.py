"""Organization management endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from app.models import OrganizationResponse
from app.auth import get_current_active_user, require_role, User
from app.database import get_db

router = APIRouter()


@router.get("/current", response_model=OrganizationResponse)
async def get_current_organization(
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db),
):
    """Get current user's organization"""
    row = await db.fetchrow(
        """
        SELECT id, name, tier, monthly_budget, current_spend, active, created_at
        FROM organizations
        WHERE id = $1
        """,
        current_user.organization_id,
    )

    if not row:
        raise HTTPException(status_code=404, detail="Organization not found")

    return OrganizationResponse(**dict(row))


@router.put("/current")
async def update_organization(
    name: str = None,
    monthly_budget: float = None,
    current_user: User = Depends(require_role("admin")),
    db=Depends(get_db),
):
    """Update organization settings (admin only)"""
    update_fields = []
    params = []
    param_count = 1

    if name:
        update_fields.append(f"name = ${param_count}")
        params.append(name)
        param_count += 1

    if monthly_budget is not None:
        update_fields.append(f"monthly_budget = ${param_count}")
        params.append(monthly_budget)
        param_count += 1

    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    params.append(current_user.organization_id)
    query = f"UPDATE organizations SET {', '.join(update_fields)} WHERE id = ${param_count}"

    await db.execute(query, *params)

    return {"message": "Organization updated successfully"}


@router.get("/usage")
async def get_organization_usage(
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db),
):
    """Get organization usage statistics"""
    # Keywords count
    keywords_count = await db.fetchval(
        "SELECT COUNT(*) FROM keywords WHERE organization_id = $1 AND active = true",
        current_user.organization_id,
    )

    # Personas count
    personas_count = await db.fetchval(
        "SELECT COUNT(*) FROM personas WHERE organization_id = $1 AND active = true",
        current_user.organization_id,
    )

    # Posts detected (this month)
    from datetime import datetime, timedelta

    this_month_start = datetime.utcnow().replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )

    posts_this_month = await db.fetchval(
        "SELECT COUNT(*) FROM detected_posts WHERE organization_id = $1 AND detected_at >= $2",
        current_user.organization_id,
        this_month_start,
    )

    # Responses generated (this month)
    responses_this_month = await db.fetchval(
        """
        SELECT COUNT(*)
        FROM generated_responses gr
        JOIN detected_posts dp ON gr.post_id = dp.id
        WHERE dp.organization_id = $1 AND gr.created_at >= $2
        """,
        current_user.organization_id,
        this_month_start,
    )

    # Current spend
    org = await db.fetchrow(
        "SELECT tier, monthly_budget, current_spend FROM organizations WHERE id = $1",
        current_user.organization_id,
    )

    # Tier limits
    tier_limits = {
        "starter": {
            "keywords": 10,
            "personas": 1,
            "blogs": 0,
        },
        "growth": {
            "keywords": 30,
            "personas": 3,
            "blogs": 15,
        },
        "enterprise": {
            "keywords": 999,
            "personas": 999,
            "blogs": 999,
        },
    }

    limits = tier_limits.get(org["tier"], tier_limits["starter"])

    return {
        "tier": org["tier"],
        "keywords": {
            "used": keywords_count,
            "limit": limits["keywords"],
            "percentage": (keywords_count / limits["keywords"]) * 100
            if limits["keywords"] > 0
            else 0,
        },
        "personas": {
            "used": personas_count,
            "limit": limits["personas"],
            "percentage": (personas_count / limits["personas"]) * 100
            if limits["personas"] > 0
            else 0,
        },
        "posts_this_month": posts_this_month,
        "responses_this_month": responses_this_month,
        "budget": {
            "monthly_limit": float(org["monthly_budget"] or 0),
            "current_spend": float(org["current_spend"] or 0),
            "remaining": float((org["monthly_budget"] or 0) - (org["current_spend"] or 0)),
            "percentage": (org["current_spend"] / org["monthly_budget"]) * 100
            if org["monthly_budget"]
            else 0,
        },
    }


@router.get("/api-key")
async def get_api_key(
    current_user: User = Depends(require_role("admin")),
    db=Depends(get_db),
):
    """Get organization API key (admin only)"""
    row = await db.fetchrow(
        "SELECT api_key FROM organizations WHERE id = $1",
        current_user.organization_id,
    )

    if not row:
        raise HTTPException(status_code=404, detail="Organization not found")

    return {"api_key": row["api_key"]}


@router.post("/api-key/regenerate")
async def regenerate_api_key(
    current_user: User = Depends(require_role("owner")),
    db=Depends(get_db),
):
    """Regenerate organization API key (owner only)"""
    import secrets

    new_api_key = f"ogt_{secrets.token_urlsafe(32)}"

    await db.execute(
        "UPDATE organizations SET api_key = $1 WHERE id = $2",
        new_api_key,
        current_user.organization_id,
    )

    return {"api_key": new_api_key}
