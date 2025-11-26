"""
Production LinkedIn scraper using Selenium
"""
import asyncio
import re
from datetime import datetime, timedelta
from typing import List, Dict, Set, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import structlog
from bs4 import BeautifulSoup

from app.config import settings
from app.database import get_db_pool
from app.message_queue import publish_message
from app.metrics import posts_processed, posts_detected, scraping_errors

logger = structlog.get_logger()


class LinkedInMonitor:
    """Production LinkedIn monitoring engine"""

    def __init__(self):
        self.driver: Optional[webdriver.Remote] = None
        self.monitored_profiles: Dict[str, Dict] = {}
        self.processed_posts: Set[str] = set()
        self.running = False
        self.logged_in = False

    async def initialize(self):
        """Initialize Selenium driver and login to LinkedIn"""
        # Setup Chrome options
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')

        if settings.PROXY_URL:
            chrome_options.add_argument(f'--proxy-server={settings.PROXY_URL}')

        # Connect to Selenium Grid
        self.driver = webdriver.Remote(
            command_executor=settings.SELENIUM_HUB_URL,
            options=chrome_options
        )

        # Login to LinkedIn
        await self.login()

        # Load monitoring configuration
        await self.load_monitoring_config()

        logger.info(
            "LinkedIn monitor initialized",
            profile_count=len(self.monitored_profiles),
        )

    async def login(self):
        """Login to LinkedIn"""
        try:
            self.driver.get("https://www.linkedin.com/login")
            await asyncio.sleep(2)

            # Find and fill email
            email_field = self.driver.find_element(By.ID, "username")
            email_field.send_keys(settings.LINKEDIN_EMAIL)

            # Find and fill password
            password_field = self.driver.find_element(By.ID, "password")
            password_field.send_keys(settings.LINKEDIN_PASSWORD)

            # Click sign in
            sign_in_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            sign_in_button.click()

            # Wait for redirect
            await asyncio.sleep(5)

            # Check if login successful
            if "feed" in self.driver.current_url or "mynetwork" in self.driver.current_url:
                self.logged_in = True
                logger.info("Successfully logged into LinkedIn")
            else:
                logger.error("LinkedIn login failed")
                raise Exception("LinkedIn login failed")

        except Exception as e:
            logger.error("Error during LinkedIn login", error=str(e))
            scraping_errors.labels(source="linkedin", error_type="login").inc()
            raise

    async def load_monitoring_config(self):
        """Load active monitoring configuration from database"""
        pool = await get_db_pool()

        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT
                    lm.id,
                    lm.organization_id,
                    lm.profile_url,
                    lm.company_url,
                    lm.hashtags,
                    lm.auto_reply,
                    lm.persona_id
                FROM linkedin_monitors lm
                WHERE lm.active = true
                """
            )

            for row in rows:
                key = row["profile_url"] or row["company_url"]
                self.monitored_profiles[key] = dict(row)

        logger.info("Monitoring configuration loaded", profiles=len(self.monitored_profiles))

    async def start_monitoring(self):
        """Start monitoring all configured profiles/companies"""
        self.running = True

        while self.running:
            try:
                for profile_url, config in self.monitored_profiles.items():
                    if not self.running:
                        break

                    await self.monitor_profile(profile_url, config)
                    await asyncio.sleep(30)  # Delay between profiles

                # Wait before next cycle
                logger.info("Monitoring cycle complete, waiting...")
                await asyncio.sleep(settings.CHECK_INTERVAL)

            except Exception as e:
                logger.error("Error in monitoring loop", error=str(e), exc_info=True)
                await asyncio.sleep(60)

    async def monitor_profile(self, profile_url: str, config: Dict):
        """Monitor a specific LinkedIn profile or company"""
        logger.info("Monitoring LinkedIn profile", url=profile_url)

        try:
            # Navigate to profile
            self.driver.get(profile_url)
            await asyncio.sleep(3)

            # Scroll to load posts
            for _ in range(3):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                await asyncio.sleep(2)

            # Get page source and parse
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'lxml')

            # Extract posts
            posts = await self.extract_posts(soup, config)

            logger.info("Extracted posts", count=len(posts), profile=profile_url)

            # Process each post
            for post in posts:
                if post["id"] not in self.processed_posts:
                    await self.process_post(post, config)
                    self.processed_posts.add(post["id"])
                    posts_processed.labels(platform="linkedin", type="post").inc()

            # Limit cache size
            if len(self.processed_posts) > 10000:
                self.processed_posts = set(list(self.processed_posts)[-5000:])

        except Exception as e:
            logger.error("Error monitoring profile", url=profile_url, error=str(e))
            scraping_errors.labels(source="linkedin", error_type="scraping").inc()

    async def extract_posts(self, soup: BeautifulSoup, config: Dict) -> List[Dict]:
        """Extract posts from LinkedIn page"""
        posts = []

        # Find post containers (LinkedIn's class names change frequently)
        post_selectors = [
            "div.feed-shared-update-v2",
            "div.occludable-update",
            "div[data-urn]"
        ]

        post_elements = []
        for selector in post_selectors:
            elements = soup.select(selector)
            if elements:
                post_elements = elements
                break

        for element in post_elements[:settings.MAX_POSTS_PER_CHECK]:
            try:
                # Extract post data
                post_data = {
                    "id": self.extract_post_id(element),
                    "author": self.extract_author(element),
                    "content": self.extract_content(element),
                    "timestamp": self.extract_timestamp(element),
                    "engagement": self.extract_engagement(element),
                    "url": self.extract_post_url(element),
                }

                if post_data["content"]:
                    posts.append(post_data)

            except Exception as e:
                logger.warning("Error extracting post", error=str(e))
                continue

        return posts

    def extract_post_id(self, element) -> str:
        """Extract unique post ID"""
        # Try data-urn attribute
        urn = element.get('data-urn', '')
        if urn:
            return urn

        # Fallback: generate from content hash
        content = element.get_text()[:100]
        return f"linkedin_{hash(content)}"

    def extract_author(self, element) -> str:
        """Extract post author name"""
        author_selectors = [
            ".feed-shared-actor__name",
            ".update-components-actor__name",
            "span.visually-hidden"
        ]

        for selector in author_selectors:
            author_elem = element.select_one(selector)
            if author_elem:
                return author_elem.get_text().strip()

        return "Unknown"

    def extract_content(self, element) -> str:
        """Extract post content"""
        content_selectors = [
            ".feed-shared-update-v2__description",
            ".feed-shared-text",
            ".break-words"
        ]

        for selector in content_selectors:
            content_elem = element.select_one(selector)
            if content_elem:
                return content_elem.get_text().strip()

        return ""

    def extract_timestamp(self, element) -> Optional[datetime]:
        """Extract post timestamp"""
        time_selectors = [
            "time",
            ".feed-shared-actor__sub-description"
        ]

        for selector in time_selectors:
            time_elem = element.select_one(selector)
            if time_elem:
                datetime_str = time_elem.get('datetime', '')
                if datetime_str:
                    try:
                        return datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
                    except:
                        pass

        return None

    def extract_engagement(self, element) -> Dict:
        """Extract engagement metrics"""
        engagement = {
            "likes": 0,
            "comments": 0,
            "shares": 0
        }

        # Extract likes
        likes_elem = element.select_one(".social-details-social-counts__reactions-count")
        if likes_elem:
            engagement["likes"] = self.parse_count(likes_elem.get_text())

        # Extract comments
        comments_elem = element.select_one(".social-details-social-counts__comments")
        if comments_elem:
            engagement["comments"] = self.parse_count(comments_elem.get_text())

        return engagement

    def parse_count(self, text: str) -> int:
        """Parse engagement count from text"""
        text = text.strip().lower()

        # Remove non-numeric characters except K, M
        match = re.search(r'(\d+(?:\.\d+)?)\s*([KM])?', text)
        if match:
            number = float(match.group(1))
            multiplier = match.group(2)

            if multiplier == 'K':
                return int(number * 1000)
            elif multiplier == 'M':
                return int(number * 1000000)
            else:
                return int(number)

        return 0

    def extract_post_url(self, element) -> str:
        """Extract post URL"""
        link_elem = element.select_one("a[href*='/feed/update/']")
        if link_elem:
            href = link_elem.get('href', '')
            if href.startswith('http'):
                return href
            else:
                return f"https://www.linkedin.com{href}"

        return ""

    async def process_post(self, post: Dict, config: Dict):
        """Process and save detected post"""
        # Calculate engagement score
        engagement_score = (
            post["engagement"]["likes"] +
            post["engagement"]["comments"] * 2 +
            post["engagement"]["shares"] * 3
        )

        # Check if post is relevant (basic keyword matching)
        # In production, this would use the keyword matcher from reddit service
        is_relevant = True  # Simplified for now

        if not is_relevant:
            return

        pool = await get_db_pool()

        async with pool.acquire() as conn:
            post_id = await conn.fetchval(
                """
                INSERT INTO detected_posts (
                    organization_id, platform, external_id, url, title, content,
                    author, engagement_score, comment_count, relevance_score,
                    metadata, priority, status
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                ON CONFLICT (platform, external_id) DO UPDATE
                SET engagement_score = EXCLUDED.engagement_score,
                    comment_count = EXCLUDED.comment_count
                RETURNING id
                """,
                config["organization_id"],
                "linkedin",
                post["id"],
                post["url"],
                "",  # LinkedIn doesn't have post titles
                post["content"],
                post["author"],
                float(engagement_score),
                post["engagement"]["comments"],
                0.8,  # Default relevance
                {
                    "likes": post["engagement"]["likes"],
                    "shares": post["engagement"]["shares"],
                },
                "medium",
                "pending",
            )

        # Publish to message queue
        await publish_message(
            "post.detected",
            {
                "post_id": str(post_id),
                "organization_id": str(config["organization_id"]),
                "platform": "linkedin",
                "priority": "medium",
                "auto_reply": config["auto_reply"],
                "persona_id": str(config["persona_id"]) if config["persona_id"] else None,
            },
        )

        posts_detected.labels(platform="linkedin", priority="medium").inc()

        logger.info(
            "Detected relevant LinkedIn post",
            post_id=post["id"],
            author=post["author"],
            engagement=engagement_score,
        )

    async def stop(self):
        """Stop monitoring and cleanup"""
        self.running = False
        if self.driver:
            self.driver.quit()
        logger.info("LinkedIn monitor stopped")
