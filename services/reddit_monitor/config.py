"""Configuration management"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""

    # Service info
    VERSION: str = "1.0.0"
    SERVICE_NAME: str = "reddit-monitor"

    # Database
    DATABASE_URL: str
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 40

    # Redis
    REDIS_URL: str
    REDIS_MAX_CONNECTIONS: int = 50

    # RabbitMQ
    RABBITMQ_URL: str

    # Reddit API
    REDDIT_CLIENT_ID: str
    REDDIT_CLIENT_SECRET: str
    REDDIT_USER_AGENT: str
    REDDIT_USERNAME: Optional[str] = None
    REDDIT_PASSWORD: Optional[str] = None

    # Monitoring configuration
    BATCH_SIZE: int = 100
    CHECK_INTERVAL: int = 30  # seconds
    MAX_POSTS_PER_SUBREDDIT: int = 500
    RELEVANCE_THRESHOLD: float = 0.6

    # Rate limiting
    REQUESTS_PER_MINUTE: int = 60

    # Retry configuration
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 5

    # Feature flags
    ENABLE_COMMENT_MONITORING: bool = True
    ENABLE_AUTO_SCORING: bool = True
    ENABLE_PUSHSHIFT_FALLBACK: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
