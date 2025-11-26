"""Configuration management"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    # Service info
    VERSION: str = "1.0.0"
    SERVICE_NAME: str = "blog-monitor"

    # Database
    DATABASE_URL: str
    DB_POOL_SIZE: int = 20

    # Redis
    REDIS_URL: str

    # RabbitMQ
    RABBITMQ_URL: str

    # Monitoring configuration
    DEFAULT_CHECK_INTERVAL: int = 3600  # 1 hour
    MAX_POSTS_PER_BLOG: int = 20
    RELEVANCE_THRESHOLD: float = 0.6

    # HTTP settings
    USER_AGENT: str = "OGTool Blog Monitor Bot/1.0"
    REQUEST_TIMEOUT: int = 30

    # Retry configuration
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 5

    # Feature flags
    ENABLE_RSS_PARSING: bool = True
    ENABLE_WEB_SCRAPING: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
