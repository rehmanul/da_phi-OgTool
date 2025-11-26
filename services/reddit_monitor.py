"""
Production Reddit Monitoring Service
Real-time Reddit monitoring with PRAW
"""
import os
import asyncio
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set
import praw
import prawcore
from sqlalchemy.orm import Session
import structlog

from database.connection import get_db
from database.models import Monitor, Lead, LeadKeyword, Keyword, Alert, LeadStatus, PlatformType
from services.lead_scorer import LeadScorer
from services.webhook_dispatcher import WebhookDispatcher

logger = structlog.get_logger()

class RedditMonitor:
    """Production Reddit monitoring service"""

    def __init__(self):
        """Initialize Reddit monitor with PRAW"""
        self.reddit_client = None
        self.lead_scorer = LeadScorer()
        self.webhook_dispatcher = WebhookDispatcher()
        self.processed_ids: Set[str] = set()
        self.is_running = False
        self.monitoring_tasks = {}

        # Reddit API credentials
        self.client_id = os.environ.get("REDDIT_CLIENT_ID", "")
        self.client_secret = os.environ.get("REDDIT_CLIENT_SECRET", "")
        self.user_agent = os.environ.get("REDDIT_USER_AGENT", "OGTool/2.0 Lead Generation Bot")

        if self.client_id and self.client_secret:
            self.initialize_reddit()

    def initialize_reddit(self):
        """Initialize Reddit client"""
        try:
            self.reddit_client = praw.Reddit(
                client_id=self.client_id,
                client_secret=self.client_secret,
                user_agent=self.user_agent,
                check_for_async=False
            )
            # Test connection
            self.reddit_client.user.me()
            logger.info("Reddit client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Reddit client: {e}")
            self.reddit_client = None

    async def start(self):
        """Start the monitoring service"""
        if not self.reddit_client:
            logger.warning("Reddit monitoring disabled - no credentials configured")
            return

        self.is_running = True
        logger.info("Starting Reddit monitoring service")

        # Start monitor check loop
        asyncio.create_task(self.monitor_check_loop())

        # Start stream monitoring for real-time data
        asyncio.create_task(self.stream_monitor())

    async def stop(self):
        """Stop the monitoring service"""
        self.is_running = False

        # Cancel all monitoring tasks
        for task_id, task in self.monitoring_tasks.items():
            task.cancel()

        logger.info("Reddit monitoring service stopped")

    async def monitor_check_loop(self):
        """Periodically check and update monitors"""
        while self.is_running:
            try:
                with get_db() as db:
                    # Get active monitors with Reddit platform
                    monitors = db.query(Monitor).filter(
                        Monitor.is_active == True,
                        Monitor.platforms.contains(["reddit"])
                    ).all()

                    for monitor in monitors:
                        # Check if it's time to run
                        if not monitor.next_check or monitor.next_check <= datetime.utcnow():
                            asyncio.create_task(self.process_monitor(monitor.id))

                            # Update next check time
                            monitor.next_check = datetime.utcnow() + timedelta(seconds=monitor.check_interval)
                            db.commit()

            except Exception as e:
                logger.error(f"Monitor check loop error: {e}")

            # Wait before next check
            await asyncio.sleep(30)

    async def process_monitor(self, monitor_id: int):
        """Process a single monitor"""
        try:
            with get_db() as db:
                monitor = db.query(Monitor).filter(Monitor.id == monitor_id).first()
                if not monitor:
                    return

                # Get keywords for this monitor
                keywords = [mk.keyword.keyword for mk in monitor.keywords]
                subreddits = monitor.subreddits or ["all"]

                logger.info(f"Processing monitor {monitor.id} with keywords: {keywords}")

                leads_found = []

                for subreddit_name in subreddits:
                    try:
                        subreddit = self.reddit_client.subreddit(subreddit_name)

                        # Search each keyword
                        for keyword in keywords:
                            try:
                                # Search posts
                                for submission in subreddit.search(
                                    keyword,
                                    sort="new",
                                    time_filter="day",
                                    limit=monitor.max_results or 25
                                ):
                                    # Skip if already processed
                                    if submission.id in self.processed_ids:
                                        continue

                                    # Create lead
                                    lead = await self.create_lead_from_submission(
                                        submission,
                                        monitor,
                                        keyword,
                                        db
                                    )
                                    if lead:
                                        leads_found.append(lead)
                                        self.processed_ids.add(submission.id)

                                # Also check hot posts
                                for submission in subreddit.hot(limit=10):
                                    if keyword.lower() in submission.title.lower() or \
                                       (submission.selftext and keyword.lower() in submission.selftext.lower()):
                                        if submission.id not in self.processed_ids:
                                            lead = await self.create_lead_from_submission(
                                                submission,
                                                monitor,
                                                keyword,
                                                db
                                            )
                                            if lead:
                                                leads_found.append(lead)
                                                self.processed_ids.add(submission.id)

                            except prawcore.exceptions.NotFound:
                                logger.warning(f"Subreddit {subreddit_name} not found")
                            except Exception as e:
                                logger.error(f"Error searching {subreddit_name} for '{keyword}': {e}")

                    except Exception as e:
                        logger.error(f"Error processing subreddit {subreddit_name}: {e}")

                # Update monitor last check
                monitor.last_check = datetime.utcnow()
                db.commit()

                # Send webhook notifications
                if leads_found and monitor.webhook_url:
                    await self.webhook_dispatcher.send_leads(monitor.webhook_url, leads_found)

                logger.info(f"Monitor {monitor.id} found {len(leads_found)} new leads")

        except Exception as e:
            logger.error(f"Error processing monitor {monitor_id}: {e}")

    async def stream_monitor(self):
        """Monitor Reddit streams for real-time data"""
        if not self.reddit_client:
            return

        while self.is_running:
            try:
                with get_db() as db:
                    # Get all active keywords
                    keywords = db.query(Keyword).filter(Keyword.is_active == True).all()
                    keyword_map = {kw.keyword.lower(): kw for kw in keywords}

                    # Monitor r/all comments stream
                    subreddit = self.reddit_client.subreddit("all")

                    for comment in subreddit.stream.comments(skip_existing=True):
                        if not self.is_running:
                            break

                        # Check for keyword matches
                        comment_lower = comment.body.lower()
                        matched_keywords = [
                            kw for kw_text, kw in keyword_map.items()
                            if kw_text in comment_lower
                        ]

                        if matched_keywords:
                            # Find relevant monitors
                            for keyword in matched_keywords:
                                monitors = db.query(Monitor).join(
                                    Monitor.keywords
                                ).filter(
                                    Monitor.is_active == True,
                                    Monitor.platforms.contains(["reddit"])
                                ).all()

                                for monitor in monitors:
                                    # Get the submission (post) the comment belongs to
                                    submission = comment.submission

                                    # Create lead from submission if not already processed
                                    if submission.id not in self.processed_ids:
                                        lead = await self.create_lead_from_submission(
                                            submission,
                                            monitor,
                                            keyword.keyword,
                                            db
                                        )
                                        if lead:
                                            self.processed_ids.add(submission.id)

                                            # Send real-time alert for high-score leads
                                            if lead.total_score >= 0.8:
                                                await self.create_alert(monitor, lead, db)

            except Exception as e:
                logger.error(f"Stream monitoring error: {e}")
                await asyncio.sleep(60)  # Wait before retrying

    async def create_lead_from_submission(
        self,
        submission,
        monitor: Monitor,
        keyword: str,
        db: Session
    ) -> Optional[Lead]:
        """Create a lead from a Reddit submission"""
        try:
            # Check if lead already exists
            existing = db.query(Lead).filter(
                Lead.platform == PlatformType.REDDIT,
                Lead.platform_id == submission.id
            ).first()

            if existing:
                return None

            # Extract content
            content = submission.selftext[:2000] if submission.selftext else ""

            # Create lead
            lead = Lead(
                monitor_id=monitor.id,
                platform=PlatformType.REDDIT,
                platform_id=submission.id,
                title=submission.title[:500],
                content=content,
                author=str(submission.author) if submission.author else "deleted",
                author_profile=f"https://reddit.com/u/{submission.author}" if submission.author else None,
                url=f"https://reddit.com{submission.permalink}",
                permalink=submission.permalink,
                subreddit=submission.subreddit.display_name,
                post_karma=submission.score,
                comment_count=submission.num_comments,
                upvote_ratio=submission.upvote_ratio if hasattr(submission, 'upvote_ratio') else 0,
                status=LeadStatus.NEW,
                posted_at=datetime.fromtimestamp(submission.created_utc),
                found_at=datetime.utcnow()
            )

            # Score the lead
            scores = self.lead_scorer.score_lead(lead, [keyword])
            lead.relevance_score = scores['relevance']
            lead.engagement_score = scores['engagement']
            lead.opportunity_score = scores['opportunity']
            lead.total_score = scores['total']

            # AI analysis would go here
            lead.ai_intent = self.detect_intent(submission.title, content)
            lead.ai_sentiment = self.detect_sentiment(submission.title, content)

            db.add(lead)
            db.commit()

            # Link keywords
            keyword_obj = db.query(Keyword).filter(
                Keyword.keyword == keyword
            ).first()

            if keyword_obj:
                lead_keyword = LeadKeyword(
                    lead_id=lead.id,
                    keyword_id=keyword_obj.id,
                    match_count=1
                )
                db.add(lead_keyword)
                db.commit()

            logger.info(f"Created lead from Reddit post: {submission.id} (score: {lead.total_score:.2f})")
            return lead

        except Exception as e:
            logger.error(f"Error creating lead from submission: {e}")
            db.rollback()
            return None

    def detect_intent(self, title: str, content: str) -> str:
        """Detect the intent of a post"""
        text = f"{title} {content}".lower()

        if any(word in text for word in ["how", "what", "why", "when", "where", "?"]):
            return "question"
        elif any(word in text for word in ["problem", "issue", "error", "broken", "fail"]):
            return "problem"
        elif any(word in text for word in ["looking for", "need", "want", "searching"]):
            return "seeking"
        elif any(word in text for word in ["love", "great", "awesome", "recommend"]):
            return "positive"
        elif any(word in text for word in ["hate", "terrible", "awful", "worst"]):
            return "negative"
        else:
            return "general"

    def detect_sentiment(self, title: str, content: str) -> str:
        """Detect sentiment of a post"""
        text = f"{title} {content}".lower()

        positive_words = ["good", "great", "excellent", "love", "best", "amazing", "wonderful"]
        negative_words = ["bad", "terrible", "hate", "worst", "awful", "horrible", "disappointing"]

        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)

        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"

    async def create_alert(self, monitor: Monitor, lead: Lead, db: Session):
        """Create an alert for high-value leads"""
        alert = Alert(
            monitor_id=monitor.id,
            type="high_score",
            severity="high",
            title=f"High-score lead found: {lead.title[:100]}",
            message=f"A lead with score {lead.total_score:.2f} was found on r/{lead.subreddit}",
            data={
                "lead_id": lead.id,
                "score": lead.total_score,
                "url": lead.url
            }
        )
        db.add(alert)
        db.commit()

        # Send webhook notification if configured
        if monitor.webhook_url:
            await self.webhook_dispatcher.send_alert(monitor.webhook_url, alert)

    def cleanup_old_processed_ids(self):
        """Clean up old processed IDs to prevent memory growth"""
        # Keep only last 10,000 IDs
        if len(self.processed_ids) > 10000:
            # Convert to list, sort by time (IDs are time-based), keep recent
            ids_list = list(self.processed_ids)
            self.processed_ids = set(ids_list[-5000:])
            logger.info(f"Cleaned up processed IDs, kept {len(self.processed_ids)}")

# Singleton instance
reddit_monitor = RedditMonitor()