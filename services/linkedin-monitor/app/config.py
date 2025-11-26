"""Configuration management"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""

    # Service info
    VERSION: str = "1.0.0"
    SERVICE_NAME: str = "linkedin-monitor"

    # Database
    DATABASE_URL: str
    DB_POOL_SIZE: int = 20

    # Redis
    REDIS_URL: str

    # RabbitMQ
    RABBITMQ_URL: str

    # LinkedIn credentials
    LINKEDIN_EMAIL: str
    LINKEDIN_PASSWORD: str

    # Selenium configuration
    SELENIUM_HUB_URL: str = "http://selenium-hub:4444/wd/hub"

    # Monitoring configuration
    CHECK_INTERVAL: int = 600  # 10 minutes
    MAX_POSTS_PER_CHECK: int = 50
    RELEVANCE_THRESHOLD: float = 0.6

    # Proxy configuration (optional)
    PROXY_URL: Optional[str] = None
    PROXY_USERNAME: Optional[str] = None
    PROXY_PASSWORD: Optional[str] = None

    # Rate limiting
    REQUESTS_PER_HOUR: int = 100

    # Retry configuration
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 10

    # Feature flags
    ENABLE_POST_MONITORING: bool = True
    ENABLE_COMMENT_MONITORING: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
