"""Analytics and reporting endpoints"""
from fastapi import APIRouter, Depends, Query
from typing import List
from datetime import datetime, timedelta
from app.models import (
    ShareOfVoiceResponse,
    KeywordRankingResponse,
    EngagementMetrics,
)
from app.auth import get_current_active_user, User
from app.database import get_db

router = APIRouter()


@router.get("/share-of-voice", response_model=List[ShareOfVoiceResponse])
async def get_share_of_voice(
    platform: str = Query(...),
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db),
):
    """Get share of voice metrics by platform"""
    # This would typically query ClickHouse for aggregated data
    # For now, querying from TimescaleDB
    start_date = datetime.utcnow() - timedelta(days=days)

    rows = await db.fetch(
        """
        SELECT
            k.keyword,
            kr.platform,
            SUM(kr.mentions_count) as total_mentions,
            AVG(kr.share_of_voice) as avg_share_of_voice
        FROM keyword_rankings kr
        JOIN keywords k ON kr.keyword_id = k.id
        WHERE kr.organization_id = $1
          AND kr.platform = $2
          AND kr.time >= $3
        GROUP BY k.keyword, kr.platform
        ORDER BY avg_share_of_voice DESC
        """,
        current_user.organization_id,
        platform,
        start_date,
    )

    results = []
    for row in rows:
        # Calculate competitors mentions (simplified)
        our_mentions = int(row["total_mentions"] * row["avg_share_of_voice"] / 100)
        competitor_mentions = row["total_mentions"] - our_mentions

        results.append(
            ShareOfVoiceResponse(
                keyword=row["keyword"],
                platform=row["platform"],
                our_mentions=our_mentions,
                competitor_mentions=competitor_mentions,
                total_mentions=row["total_mentions"],
                share_percentage=row["avg_share_of_voice"],
                period=f"{days} days",
            )
        )

    return results


@router.get("/keyword-rankings", response_model=List[KeywordRankingResponse])
async def get_keyword_rankings(
    platform: str = Query(...),
    days: int = Query(7, ge=1, le=90),
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db),
):
    """Get keyword ranking trends"""
    start_date = datetime.utcnow() - timedelta(days=days)

    rows = await db.fetch(
        """
        SELECT
            k.keyword,
            kr.platform,
            kr.position,
            kr.mentions_count,
            kr.share_of_voice,
            kr.time
        FROM keyword_rankings kr
        JOIN keywords k ON kr.keyword_id = k.id
        WHERE kr.organization_id = $1
          AND kr.platform = $2
          AND kr.time >= $3
        ORDER BY kr.time DESC, kr.position ASC
        LIMIT 100
        """,
        current_user.organization_id,
        platform,
        start_date,
    )

    return [KeywordRankingResponse(**dict(row)) for row in rows]


@router.get("/engagement", response_model=EngagementMetrics)
async def get_engagement_metrics(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db),
):
    """Get engagement metrics summary"""
    start_date = datetime.utcnow() - timedelta(days=days)

    # Posts detected
    total_posts = await db.fetchval(
        """
        SELECT COUNT(*)
        FROM detected_posts
        WHERE organization_id = $1 AND detected_at >= $2
        """,
        current_user.organization_id,
        start_date,
    )

    # Responses generated
    responses_generated = await db.fetchval(
        """
        SELECT COUNT(*)
        FROM generated_responses gr
        JOIN detected_posts dp ON gr.post_id = dp.id
        WHERE dp.organization_id = $1 AND gr.created_at >= $2
        """,
        current_user.organization_id,
        start_date,
    )

    # Responses posted
    responses_posted = await db.fetchval(
        """
        SELECT COUNT(*)
        FROM generated_responses gr
        JOIN detected_posts dp ON gr.post_id = dp.id
        WHERE dp.organization_id = $1
          AND gr.posted = true
          AND gr.posted_at >= $2
        """,
        current_user.organization_id,
        start_date,
    )

    # Average engagement score
    avg_engagement = await db.fetchval(
        """
        SELECT AVG(engagement_score)
        FROM detected_posts
        WHERE organization_id = $1 AND detected_at >= $2
        """,
        current_user.organization_id,
        start_date,
    ) or 0.0

    # Average quality score
    avg_quality = await db.fetchval(
        """
        SELECT AVG(gr.quality_score)
        FROM generated_responses gr
        JOIN detected_posts dp ON gr.post_id = dp.id
        WHERE dp.organization_id = $1 AND gr.created_at >= $2
        """,
        current_user.organization_id,
        start_date,
    ) or 0.0

    # Conversions (would come from attribution tracking)
    conversion_count = 0  # TODO: Implement conversion attribution

    return EngagementMetrics(
        total_posts_detected=total_posts or 0,
        responses_generated=responses_generated or 0,
        responses_posted=responses_posted or 0,
        avg_engagement_score=float(avg_engagement),
        avg_quality_score=float(avg_quality),
        conversion_count=conversion_count,
        period=f"{days} days",
    )


@router.get("/cost")
async def get_cost_metrics(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db),
):
    """Get cost metrics"""
    start_date = datetime.utcnow() - timedelta(days=days)

    # Total cost from responses
    total_cost = await db.fetchval(
        """
        SELECT COALESCE(SUM(gr.cost), 0)
        FROM generated_responses gr
        JOIN detected_posts dp ON gr.post_id = dp.id
        WHERE dp.organization_id = $1 AND gr.created_at >= $2
        """,
        current_user.organization_id,
        start_date,
    )

    # Get organization budget
    org = await db.fetchrow(
        "SELECT monthly_budget, current_spend FROM organizations WHERE id = $1",
        current_user.organization_id,
    )

    return {
        "total_cost": float(total_cost or 0),
        "monthly_budget": float(org["monthly_budget"] or 0),
        "current_spend": float(org["current_spend"] or 0),
        "remaining_budget": float((org["monthly_budget"] or 0) - (org["current_spend"] or 0)),
        "period_days": days,
    }
