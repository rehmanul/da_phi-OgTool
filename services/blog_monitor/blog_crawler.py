"""
Production blog monitoring with RSS and web scraping
"""
import asyncio
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Set, Optional
import feedparser
import aiohttp
from bs4 import BeautifulSoup
import trafilatura
import structlog

from app.config import settings
from app.database import get_db_pool
from app.message_queue import publish_message
from app.metrics import posts_processed, posts_detected, fetch_errors

logger = structlog.get_logger()


class BlogMonitor:
    """Production blog monitoring engine"""

    def __init__(self):
        self.monitored_blogs: Dict[str, Dict] = {}
        self.processed_posts: Set[str] = set()
        self.running = False
        self.session: Optional[aiohttp.ClientSession] = None

    async def initialize(self):
        """Initialize HTTP session and load monitoring configuration"""
        # Create HTTP session
        self.session = aiohttp.ClientSession(
            headers={"User-Agent": settings.USER_AGENT},
            timeout=aiohttp.ClientTimeout(total=settings.REQUEST_TIMEOUT),
        )

        # Load monitoring configuration
        await self.load_monitoring_config()

        logger.info(
            "Blog monitor initialized",
            blog_count=len(self.monitored_blogs),
        )

    async def load_monitoring_config(self):
        """Load active monitoring configuration from database"""
        pool = await get_db_pool()

        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT
                    bm.id,
                    bm.organization_id,
                    bm.blog_url,
                    bm.blog_name,
                    bm.rss_feed,
                    bm.check_frequency,
                    bm.last_checked
                FROM blog_monitors bm
                WHERE bm.active = true
                """
            )

            for row in rows:
                self.monitored_blogs[row["blog_url"]] = dict(row)

        logger.info("Monitoring configuration loaded", blogs=len(self.monitored_blogs))

    async def start_monitoring(self):
        """Start monitoring all configured blogs"""
        self.running = True

        while self.running:
            try:
                tasks = []
                for blog_url, config in self.monitored_blogs.items():
                    # Check if it's time to check this blog
                    if self.should_check_blog(config):
                        tasks.append(self.monitor_blog(blog_url, config))

                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)

                # Wait before next cycle
                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                logger.error("Error in monitoring loop", error=str(e), exc_info=True)
                await asyncio.sleep(60)

    def should_check_blog(self, config: Dict) -> bool:
        """Check if blog should be checked now"""
        if not config.get("last_checked"):
            return True

        next_check = config["last_checked"] + timedelta(seconds=config["check_frequency"])
        return datetime.utcnow() >= next_check

    async def monitor_blog(self, blog_url: str, config: Dict):
        """Monitor a specific blog"""
        logger.info("Monitoring blog", url=blog_url)

        try:
            # Try RSS feed first
            posts = []
            if config["rss_feed"] and settings.ENABLE_RSS_PARSING:
                posts = await self.fetch_rss_posts(config["rss_feed"], config)

            # Fallback to web scraping if no RSS or no posts
            if not posts and settings.ENABLE_WEB_SCRAPING:
                posts = await self.scrape_blog_posts(blog_url, config)

            logger.info("Fetched blog posts", count=len(posts), blog=blog_url)

            # Process each post
            for post in posts:
                post_hash = self.generate_post_hash(post)
                if post_hash not in self.processed_posts:
                    await self.process_post(post, config)
                    self.processed_posts.add(post_hash)
                    posts_processed.labels(platform="blog", type="post").inc()

            # Update last checked time
            await self.update_last_checked(config["id"])

            # Limit cache size
            if len(self.processed_posts) > 10000:
                self.processed_posts = set(list(self.processed_posts)[-5000:])

        except Exception as e:
            logger.error("Error monitoring blog", url=blog_url, error=str(e))
            fetch_errors.labels(source="blog", error_type="fetch").inc()

    async def fetch_rss_posts(self, rss_url: str, config: Dict) -> List[Dict]:
        """Fetch posts from RSS feed"""
        posts = []

        try:
            async with self.session.get(rss_url) as response:
                if response.status != 200:
                    logger.warning("RSS fetch failed", url=rss_url, status=response.status)
                    return posts

                content = await response.text()

            # Parse RSS feed
            feed = feedparser.parse(content)

            for entry in feed.entries[:settings.MAX_POSTS_PER_BLOG]:
                post = {
                    "title": entry.get("title", ""),
                    "url": entry.get("link", ""),
                    "content": self.extract_rss_content(entry),
                    "author": entry.get("author", "Unknown"),
                    "published": self.parse_published_date(entry),
                    "source": "rss",
                }

                # Only include recent posts (last 7 days)
                if post["published"]:
                    age = datetime.utcnow() - post["published"]
                    if age > timedelta(days=7):
                        continue

                posts.append(post)

            logger.info("Fetched RSS posts", count=len(posts), url=rss_url)

        except Exception as e:
            logger.error("Error fetching RSS", url=rss_url, error=str(e))
            fetch_errors.labels(source="rss", error_type="parse").inc()

        return posts

    def extract_rss_content(self, entry) -> str:
        """Extract content from RSS entry"""
        # Try different content fields
        if hasattr(entry, "content"):
            return entry.content[0].value if entry.content else ""
        elif hasattr(entry, "summary"):
            return entry.summary
        elif hasattr(entry, "description"):
            return entry.description
        return ""

    def parse_published_date(self, entry) -> Optional[datetime]:
        """Parse published date from RSS entry"""
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            from time import struct_time
            import calendar

            return datetime.utcfromtimestamp(calendar.timegm(entry.published_parsed))

        return None

    async def scrape_blog_posts(self, blog_url: str, config: Dict) -> List[Dict]:
        """Scrape blog posts from website"""
        posts = []

        try:
            async with self.session.get(blog_url) as response:
                if response.status != 200:
                    logger.warning("Blog fetch failed", url=blog_url, status=response.status)
                    return posts

                html = await response.text()

            # Parse HTML
            soup = BeautifulSoup(html, 'lxml')

            # Find article links (common patterns)
            article_links = set()

            # Try common selectors
            selectors = [
                "article a[href]",
                ".post a[href]",
                ".entry a[href]",
                "h2 a[href]",
                "h3 a[href]",
            ]

            for selector in selectors:
                links = soup.select(selector)
                for link in links:
                    href = link.get('href', '')
                    if href and self.is_article_url(href, blog_url):
                        article_links.add(self.normalize_url(href, blog_url))

            # Fetch and parse each article
            for url in list(article_links)[:settings.MAX_POSTS_PER_BLOG]:
                article = await self.scrape_article(url)
                if article:
                    posts.append(article)
                await asyncio.sleep(1)  # Be polite

            logger.info("Scraped blog posts", count=len(posts), blog=blog_url)

        except Exception as e:
            logger.error("Error scraping blog", url=blog_url, error=str(e))
            fetch_errors.labels(source="blog", error_type="scrape").inc()

        return posts

    def is_article_url(self, url: str, base_url: str) -> bool:
        """Check if URL looks like an article"""
        # Skip navigation and non-article pages
        skip_patterns = [
            "/tag/", "/category/", "/page/", "/author/",
            "mailto:", "javascript:", "#", "/search",
        ]

        url_lower = url.lower()
        for pattern in skip_patterns:
            if pattern in url_lower:
                return False

        return True

    def normalize_url(self, url: str, base_url: str) -> str:
        """Normalize URL to absolute"""
        from urllib.parse import urljoin
        return urljoin(base_url, url)

    async def scrape_article(self, url: str) -> Optional[Dict]:
        """Scrape a single article"""
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    return None

                html = await response.text()

            # Extract content using trafilatura (best practice for article extraction)
            content = trafilatura.extract(html, include_comments=False, include_tables=False)

            if not content:
                return None

            # Extract title and other metadata
            soup = BeautifulSoup(html, 'lxml')
            title = self.extract_title(soup)
            author = self.extract_author(soup)

            return {
                "title": title,
                "url": url,
                "content": content,
                "author": author,
                "published": datetime.utcnow(),  # Approximate
                "source": "scrape",
            }

        except Exception as e:
            logger.warning("Error scraping article", url=url, error=str(e))
            return None

    def extract_title(self, soup: BeautifulSoup) -> str:
        """Extract article title"""
        # Try different title selectors
        selectors = ["h1", "article h1", ".entry-title", ".post-title"]

        for selector in selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                return title_elem.get_text().strip()

        # Fallback to page title
        title_tag = soup.find("title")
        if title_tag:
            return title_tag.get_text().strip()

        return "Untitled"

    def extract_author(self, soup: BeautifulSoup) -> str:
        """Extract article author"""
        selectors = [
            ".author-name",
            ".author",
            ".by-author",
            'meta[name="author"]',
        ]

        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                if elem.name == "meta":
                    return elem.get("content", "Unknown")
                return elem.get_text().strip()

        return "Unknown"

    def generate_post_hash(self, post: Dict) -> str:
        """Generate unique hash for post"""
        content = f"{post['url']}:{post['title']}"
        return hashlib.md5(content.encode()).hexdigest()

    async def process_post(self, post: Dict, config: Dict):
        """Process and save detected post"""
        # Calculate relevance (simplified)
        relevance_score = 0.7  # Would use keyword matching in production

        if relevance_score < settings.RELEVANCE_THRESHOLD:
            return

        pool = await get_db_pool()

        async with pool.acquire() as conn:
            post_id = await conn.fetchval(
                """
                INSERT INTO detected_posts (
                    organization_id, platform, external_id, url, title, content,
                    author, engagement_score, relevance_score, metadata,
                    priority, status
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                ON CONFLICT (platform, external_id) DO NOTHING
                RETURNING id
                """,
                config["organization_id"],
                "blog",
                self.generate_post_hash(post),
                post["url"],
                post["title"],
                post["content"][:5000],  # Limit content length
                post["author"],
                5.0,  # Default engagement
                relevance_score,
                {
                    "source": post["source"],
                    "published": post["published"].isoformat() if post["published"] else None,
                },
                "medium",
                "pending",
            )

            if not post_id:
                return  # Already exists

        # Publish to message queue
        await publish_message(
            "post.detected",
            {
                "post_id": str(post_id),
                "organization_id": str(config["organization_id"]),
                "platform": "blog",
                "priority": "medium",
                "auto_reply": False,
                "persona_id": None,
            },
        )

        posts_detected.labels(platform="blog", priority="medium").inc()

        logger.info(
            "Detected blog post",
            title=post["title"][:50],
            url=post["url"],
        )

    async def update_last_checked(self, monitor_id: str):
        """Update last checked timestamp"""
        pool = await get_db_pool()

        async with pool.acquire() as conn:
            await conn.execute(
                "UPDATE blog_monitors SET last_checked = NOW() WHERE id = $1",
                monitor_id,
            )

    async def stop(self):
        """Stop monitoring and cleanup"""
        self.running = False
        if self.session:
            await self.session.close()
        logger.info("Blog monitor stopped")
