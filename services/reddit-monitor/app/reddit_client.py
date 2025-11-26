"""
Production Reddit monitoring implementation with real-time keyword tracking
"""
import asyncio
import re
from datetime import datetime, timedelta
from typing import List, Dict, Set, Optional
import asyncpraw
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.database import get_db_pool
from app.message_queue import publish_message
from app.scoring import calculate_relevance_score, calculate_engagement_score
from app.keyword_matcher import KeywordMatcher
from app.metrics import (
    posts_processed,
    posts_detected,
    api_errors,
    processing_time,
)

logger = structlog.get_logger()


class RedditMonitor:
    """Production Reddit monitoring engine"""

    def __init__(self):
        self.reddit: Optional[asyncpraw.Reddit] = None
        self.keyword_matcher = KeywordMatcher()
        self.monitored_subreddits: Dict[str, Dict] = {}
        self.processed_posts: Set[str] = set()  # Cache to avoid reprocessing
        self.running = False

    async def initialize(self):
        """Initialize Reddit API client and load monitoring configuration"""
        # Initialize Reddit client
        self.reddit = asyncpraw.Reddit(
            client_id=settings.REDDIT_CLIENT_ID,
            client_secret=settings.REDDIT_CLIENT_SECRET,
            user_agent=settings.REDDIT_USER_AGENT,
            username=settings.REDDIT_USERNAME,
            password=settings.REDDIT_PASSWORD,
            ratelimit_seconds=300,
        )

        # Load monitoring configuration from database
        await self.load_monitoring_config()

        logger.info(
            "Reddit monitor initialized",
            subreddit_count=len(self.monitored_subreddits),
            keyword_count=self.keyword_matcher.get_keyword_count(),
        )

    async def load_monitoring_config(self):
        """Load active monitoring configuration from database"""
        pool = await get_db_pool()

        async with pool.acquire() as conn:
            # Load subreddit monitors with their keywords
            query = """
                SELECT
                    sm.id,
                    sm.organization_id,
                    sm.subreddit,
                    sm.engagement_threshold,
                    sm.auto_reply,
                    sm.persona_id,
                    ARRAY_AGG(k.keyword) as keywords,
                    ARRAY_AGG(k.id) as keyword_ids,
                    ARRAY_AGG(k.priority) as priorities
                FROM subreddit_monitors sm
                LEFT JOIN subreddit_keywords sk ON sm.id = sk.subreddit_monitor_id
                LEFT JOIN keywords k ON sk.keyword_id = k.id
                WHERE sm.active = true
                GROUP BY sm.id, sm.organization_id, sm.subreddit,
                         sm.engagement_threshold, sm.auto_reply, sm.persona_id
            """
            rows = await conn.fetch(query)

            for row in rows:
                subreddit = row["subreddit"].lower()
                self.monitored_subreddits[subreddit] = {
                    "id": row["id"],
                    "organization_id": row["organization_id"],
                    "engagement_threshold": row["engagement_threshold"],
                    "auto_reply": row["auto_reply"],
                    "persona_id": row["persona_id"],
                    "keywords": row["keywords"] or [],
                    "keyword_ids": row["keyword_ids"] or [],
                    "priorities": row["priorities"] or [],
                }

                # Register keywords with matcher
                for keyword, keyword_id, priority in zip(
                    row["keywords"] or [],
                    row["keyword_ids"] or [],
                    row["priorities"] or [],
                ):
                    if keyword:
                        self.keyword_matcher.add_keyword(
                            keyword=keyword,
                            keyword_id=str(keyword_id),
                            organization_id=str(row["organization_id"]),
                            priority=priority or 50,
                        )

        logger.info("Monitoring configuration loaded", subreddits=len(self.monitored_subreddits))

    async def start_monitoring(self):
        """Start monitoring all configured subreddits"""
        self.running = True

        tasks = [
            self.monitor_subreddit(subreddit, config)
            for subreddit, config in self.monitored_subreddits.items()
        ]

        # Add refresh config task
        tasks.append(self.refresh_config_periodically())

        await asyncio.gather(*tasks, return_exceptions=True)

    async def refresh_config_periodically(self):
        """Periodically refresh monitoring configuration"""
        while self.running:
            try:
                await asyncio.sleep(300)  # Refresh every 5 minutes
                logger.info("Refreshing monitoring configuration")
                await self.load_monitoring_config()
            except Exception as e:
                logger.error("Error refreshing config", error=str(e))

    @retry(
        stop=stop_after_attempt(settings.MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def monitor_subreddit(self, subreddit: str, config: Dict):
        """Monitor a specific subreddit for new posts and comments"""
        logger.info("Starting subreddit monitor", subreddit=subreddit)

        subreddit_obj = await self.reddit.subreddit(subreddit)

        while self.running:
            try:
                # Monitor new posts
                await self.process_new_posts(subreddit_obj, config)

                # Monitor new comments if enabled
                if settings.ENABLE_COMMENT_MONITORING:
                    await self.process_new_comments(subreddit_obj, config)

                await asyncio.sleep(settings.CHECK_INTERVAL)

            except asyncpraw.exceptions.Forbidden:
                logger.error("Forbidden access to subreddit", subreddit=subreddit)
                api_errors.labels(service="reddit", error_type="forbidden").inc()
                break

            except asyncpraw.exceptions.NotFound:
                logger.error("Subreddit not found", subreddit=subreddit)
                api_errors.labels(service="reddit", error_type="not_found").inc()
                break

            except Exception as e:
                logger.error(
                    "Error monitoring subreddit",
                    subreddit=subreddit,
                    error=str(e),
                    exc_info=True,
                )
                api_errors.labels(service="reddit", error_type="unknown").inc()
                await asyncio.sleep(30)

    async def process_new_posts(self, subreddit, config: Dict):
        """Process new posts from a subreddit"""
        start_time = datetime.now()
        processed_count = 0

        try:
            async for submission in subreddit.new(limit=settings.MAX_POSTS_PER_SUBREDDIT):
                # Skip if already processed
                if submission.id in self.processed_posts:
                    continue

                # Skip if too old (more than 24 hours)
                post_age = datetime.utcnow() - datetime.fromtimestamp(submission.created_utc)
                if post_age > timedelta(hours=24):
                    continue

                # Check if post matches keywords
                matches = await self.check_post_relevance(submission, config)

                if matches:
                    await self.save_detected_post(submission, config, matches)
                    processed_count += 1

                self.processed_posts.add(submission.id)
                posts_processed.labels(platform="reddit", type="post").inc()

                # Limit cache size
                if len(self.processed_posts) > 10000:
                    self.processed_posts = set(list(self.processed_posts)[-5000:])

                await asyncio.sleep(0.1)  # Rate limiting

        except Exception as e:
            logger.error("Error processing posts", error=str(e))

        processing_time.labels(service="reddit-monitor", operation="process_posts").observe(
            (datetime.now() - start_time).total_seconds()
        )

        if processed_count > 0:
            logger.info(
                "Processed posts",
                subreddit=subreddit.display_name,
                count=processed_count,
            )

    async def process_new_comments(self, subreddit, config: Dict):
        """Process new comments from a subreddit"""
        try:
            async for comment in subreddit.comments(limit=settings.BATCH_SIZE):
                if comment.id in self.processed_posts:
                    continue

                # Check if comment matches keywords
                matches = await self.check_comment_relevance(comment, config)

                if matches:
                    await self.save_detected_comment(comment, config, matches)

                self.processed_posts.add(comment.id)
                posts_processed.labels(platform="reddit", type="comment").inc()

                await asyncio.sleep(0.1)

        except Exception as e:
            logger.error("Error processing comments", error=str(e))

    async def check_post_relevance(self, submission, config: Dict) -> Optional[Dict]:
        """Check if a post is relevant based on keywords and scoring"""
        # Combine title and selftext for matching
        content = f"{submission.title} {submission.selftext}"

        # Match keywords
        matched_keywords = self.keyword_matcher.match(
            text=content, organization_id=config["organization_id"]
        )

        if not matched_keywords:
            return None

        # Calculate relevance score
        relevance_score = calculate_relevance_score(
            text=content,
            keywords=matched_keywords,
            title=submission.title,
        )

        # Calculate engagement score
        engagement_score = calculate_engagement_score(
            upvotes=submission.score,
            comments=submission.num_comments,
            post_age_hours=(
                datetime.utcnow() - datetime.fromtimestamp(submission.created_utc)
            ).total_seconds()
            / 3600,
        )

        # Check thresholds
        if relevance_score < settings.RELEVANCE_THRESHOLD:
            return None

        if engagement_score < config["engagement_threshold"]:
            return None

        return {
            "keywords": matched_keywords,
            "relevance_score": relevance_score,
            "engagement_score": engagement_score,
        }

    async def check_comment_relevance(self, comment, config: Dict) -> Optional[Dict]:
        """Check if a comment is relevant"""
        matched_keywords = self.keyword_matcher.match(
            text=comment.body, organization_id=config["organization_id"]
        )

        if not matched_keywords:
            return None

        relevance_score = calculate_relevance_score(
            text=comment.body, keywords=matched_keywords, title=""
        )

        if relevance_score < settings.RELEVANCE_THRESHOLD:
            return None

        return {
            "keywords": matched_keywords,
            "relevance_score": relevance_score,
            "engagement_score": comment.score,
        }

    async def save_detected_post(self, submission, config: Dict, matches: Dict):
        """Save detected post to database and publish to message queue"""
        pool = await get_db_pool()

        # Determine priority based on engagement and relevance
        priority = "medium"
        if matches["engagement_score"] > 50 and matches["relevance_score"] > 0.8:
            priority = "urgent"
        elif matches["engagement_score"] > 20 and matches["relevance_score"] > 0.7:
            priority = "high"

        async with pool.acquire() as conn:
            query = """
                INSERT INTO detected_posts (
                    organization_id, platform, external_id, url, title, content,
                    author, author_profile_url, subreddit, engagement_score,
                    comment_count, relevance_score, sentiment_score,
                    keyword_matches, metadata, priority, status
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
                ON CONFLICT (platform, external_id) DO UPDATE
                SET engagement_score = EXCLUDED.engagement_score,
                    comment_count = EXCLUDED.comment_count,
                    updated_at = NOW()
                RETURNING id
            """

            post_id = await conn.fetchval(
                query,
                config["organization_id"],
                "reddit",
                submission.id,
                f"https://reddit.com{submission.permalink}",
                submission.title,
                submission.selftext,
                str(submission.author) if submission.author else "[deleted]",
                f"https://reddit.com/user/{submission.author}" if submission.author else None,
                submission.subreddit.display_name,
                float(matches["engagement_score"]),
                submission.num_comments,
                float(matches["relevance_score"]),
                0.0,  # Sentiment score calculated later
                [kw["keyword"] for kw in matches["keywords"]],
                {
                    "upvote_ratio": submission.upvote_ratio,
                    "created_utc": submission.created_utc,
                    "is_self": submission.is_self,
                    "link_flair_text": submission.link_flair_text,
                },
                priority,
                "pending",
            )

        # Publish to message queue for AI processing
        await publish_message(
            queue="post.detected",
            message={
                "post_id": str(post_id),
                "organization_id": str(config["organization_id"]),
                "platform": "reddit",
                "priority": priority,
                "auto_reply": config["auto_reply"],
                "persona_id": str(config["persona_id"]) if config["persona_id"] else None,
            },
        )

        posts_detected.labels(platform="reddit", priority=priority).inc()

        logger.info(
            "Detected relevant post",
            post_id=submission.id,
            subreddit=submission.subreddit.display_name,
            title=submission.title[:100],
            relevance=matches["relevance_score"],
            engagement=matches["engagement_score"],
        )

    async def save_detected_comment(self, comment, config: Dict, matches: Dict):
        """Save detected comment to database"""
        pool = await get_db_pool()

        async with pool.acquire() as conn:
            # Get parent submission URL
            await comment.submission.load()
            parent_url = f"https://reddit.com{comment.submission.permalink}"

            query = """
                INSERT INTO detected_posts (
                    organization_id, platform, external_id, url, parent_url,
                    title, content, author, author_profile_url, subreddit,
                    engagement_score, relevance_score, keyword_matches,
                    metadata, priority, status
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
                ON CONFLICT (platform, external_id) DO NOTHING
                RETURNING id
            """

            post_id = await conn.fetchval(
                query,
                config["organization_id"],
                "reddit",
                comment.id,
                f"https://reddit.com{comment.permalink}",
                parent_url,
                comment.submission.title if hasattr(comment, "submission") else "",
                comment.body,
                str(comment.author) if comment.author else "[deleted]",
                f"https://reddit.com/user/{comment.author}" if comment.author else None,
                comment.subreddit.display_name,
                float(comment.score),
                float(matches["relevance_score"]),
                [kw["keyword"] for kw in matches["keywords"]],
                {"created_utc": comment.created_utc, "is_comment": True},
                "medium",
                "pending",
            )

            if post_id:
                logger.info("Detected relevant comment", comment_id=comment.id)

    async def stop(self):
        """Stop monitoring"""
        self.running = False
        if self.reddit:
            await self.reddit.close()
        logger.info("Reddit monitor stopped")
