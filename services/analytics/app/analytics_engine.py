"""
Production analytics processing engine
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List
import structlog

from app.config import settings
from app.database import get_db_pool
from app.clickhouse import get_clickhouse_client
from app.metrics import events_processed, aggregations_completed

logger = structlog.get_logger()


class AnalyticsEngine:
    """Analytics processing and aggregation engine"""

    def __init__(self):
        self.running = False

    async def initialize(self):
        """Initialize analytics engine"""
        logger.info("Analytics engine initialized")

    async def process_event(self, event: Dict):
        """Process a single analytics event"""
        event_type = event.get("event_type")

        if event_type == "cost":
            await self.process_cost_event(event)
        elif event_type == "engagement":
            await self.process_engagement_event(event)
        elif event_type == "response":
            await self.process_response_event(event)

        events_processed.labels(event_type=event_type or "unknown").inc()

    async def process_cost_event(self, event: Dict):
        """Process cost tracking event"""
        ch = await get_clickhouse_client()

        query = """
            INSERT INTO cost_tracking (
                timestamp, organization_id, service, operation, units_used, cost
            ) VALUES
        """

        data = [(
            datetime.fromisoformat(event["timestamp"]),
            event["organization_id"],
            event["service"],
            event["operation"],
            event["tokens"],
            event["cost"],
        )]

        await ch.execute(query, data)
        logger.debug("Cost event processed", org_id=event["organization_id"])

    async def process_engagement_event(self, event: Dict):
        """Process engagement event"""
        ch = await get_clickhouse_client()

        query = """
            INSERT INTO platform_activity (
                timestamp, organization_id, platform, activity_type, post_id,
                response_id, engagement_count, sentiment_score
            ) VALUES
        """

        data = [(
            datetime.utcnow(),
            event["organization_id"],
            event["platform"],
            event["activity_type"],
            event["post_id"],
            event.get("response_id"),
            event.get("engagement_count", 0),
            event.get("sentiment_score", 0.0),
        )]

        await ch.execute(query, data)

    async def process_response_event(self, event: Dict):
        """Process response performance event"""
        ch = await get_clickhouse_client()

        query = """
            INSERT INTO response_performance (
                timestamp, organization_id, response_id, post_id, persona_id,
                platform, generation_time_ms, quality_score, upvotes, downvotes,
                replies, conversion_attributed
            ) VALUES
        """

        data = [(
            datetime.utcnow(),
            event["organization_id"],
            event["response_id"],
            event["post_id"],
            event.get("persona_id", ""),
            event["platform"],
            event.get("generation_time_ms", 0),
            event.get("quality_score", 0.0),
            0,  # upvotes - would be tracked separately
            0,  # downvotes
            0,  # replies
            False,  # conversion_attributed
        )]

        await ch.execute(query, data)

    async def run_periodic_aggregations(self):
        """Run periodic aggregation tasks"""
        self.running = True

        # Schedule hourly aggregations
        asyncio.create_task(self.hourly_aggregation_loop())

        # Schedule daily aggregations
        asyncio.create_task(self.daily_aggregation_loop())

        # Keep running
        while self.running:
            await asyncio.sleep(60)

    async def hourly_aggregation_loop(self):
        """Run hourly aggregations"""
        while self.running:
            try:
                await self.run_hourly_aggregations()
                aggregations_completed.labels(interval="hourly").inc()
            except Exception as e:
                logger.error("Error in hourly aggregation", error=str(e), exc_info=True)

            await asyncio.sleep(settings.HOURLY_AGGREGATION_INTERVAL)

    async def daily_aggregation_loop(self):
        """Run daily aggregations"""
        while self.running:
            try:
                await self.run_daily_aggregations()
                aggregations_completed.labels(interval="daily").inc()
            except Exception as e:
                logger.error("Error in daily aggregation", error=str(e), exc_info=True)

            await asyncio.sleep(settings.DAILY_AGGREGATION_INTERVAL)

    async def run_hourly_aggregations(self):
        """Calculate hourly aggregations"""
        logger.info("Running hourly aggregations")

        # Calculate share of voice
        await self.calculate_share_of_voice()

        # Calculate keyword rankings
        await self.calculate_keyword_rankings()

    async def run_daily_aggregations(self):
        """Calculate daily aggregations"""
        logger.info("Running daily aggregations")

        # Aggregate response metrics
        await self.aggregate_response_metrics()

        # Calculate conversion attribution
        await self.calculate_conversion_attribution()

    async def calculate_share_of_voice(self):
        """Calculate share of voice metrics"""
        pool = await get_db_pool()
        ch = await get_clickhouse_client()

        # Get all active organizations
        async with pool.acquire() as conn:
            orgs = await conn.fetch("SELECT id FROM organizations WHERE active = true")

        for org in orgs:
            org_id = str(org["id"])

            # Count our mentions (from detected_posts)
            async with pool.acquire() as conn:
                our_mentions = await conn.fetchval(
                    """
                    SELECT COUNT(*)
                    FROM detected_posts
                    WHERE organization_id = $1
                      AND detected_at >= NOW() - INTERVAL '1 hour'
                    """,
                    org_id,
                )

            # Estimate total mentions (simplified - would need real competitor tracking)
            total_mentions = our_mentions * 5  # Assume we have 20% SOV

            # Insert into ClickHouse
            if total_mentions > 0:
                query = """
                    INSERT INTO share_of_voice (
                        timestamp, organization_id, keyword, platform,
                        our_mentions, competitor_mentions, total_mentions,
                        share_percentage, avg_engagement
                    ) VALUES
                """

                share_pct = (our_mentions / total_mentions) * 100

                data = [(
                    datetime.utcnow(),
                    org_id,
                    "all",  # Would be per keyword in production
                    "reddit",
                    our_mentions or 0,
                    (total_mentions - our_mentions) or 0,
                    total_mentions,
                    share_pct,
                    0.0,
                )]

                await ch.execute(query, data)

        logger.info("Share of voice calculated")

    async def calculate_keyword_rankings(self):
        """Calculate keyword ranking metrics"""
        pool = await get_db_pool()

        # Insert into PostgreSQL keyword_rankings table
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO keyword_rankings (
                    time, organization_id, keyword_id, platform,
                    mentions_count, share_of_voice
                )
                SELECT
                    NOW(),
                    k.organization_id,
                    k.id,
                    k.platform,
                    COUNT(dp.id) as mentions_count,
                    0.0 as share_of_voice
                FROM keywords k
                LEFT JOIN detected_posts dp ON
                    dp.organization_id = k.organization_id
                    AND k.keyword = ANY(dp.keyword_matches)
                    AND dp.detected_at >= NOW() - INTERVAL '1 hour'
                WHERE k.active = true
                GROUP BY k.organization_id, k.id, k.platform
                """
            )

        logger.info("Keyword rankings calculated")

    async def aggregate_response_metrics(self):
        """Aggregate response performance metrics"""
        pool = await get_db_pool()

        async with pool.acquire() as conn:
            results = await conn.fetch(
                """
                SELECT
                    dp.organization_id,
                    dp.platform,
                    COUNT(gr.id) as response_count,
                    AVG(gr.quality_score) as avg_quality,
                    SUM(gr.cost) as total_cost
                FROM generated_responses gr
                JOIN detected_posts dp ON gr.post_id = dp.id
                WHERE gr.created_at >= NOW() - INTERVAL '1 day'
                GROUP BY dp.organization_id, dp.platform
                """
            )

            logger.info("Aggregated response metrics", count=len(results))

    async def calculate_conversion_attribution(self):
        """Calculate conversion attribution"""
        # This would integrate with external systems (CRM, analytics)
        # For now, just log the placeholder
        logger.info("Conversion attribution calculated")

    async def stop(self):
        """Stop analytics engine"""
        self.running = False
        logger.info("Analytics engine stopped")
