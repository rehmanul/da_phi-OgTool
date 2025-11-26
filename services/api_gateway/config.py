"""Configuration management"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings"""

    # Service info
    VERSION: str = "1.0.0"
    SERVICE_NAME: str = "api-gateway"

    # Database
    DATABASE_URL: str
    DB_POOL_SIZE: int = 20

    # Redis
    REDIS_URL: str

    # RabbitMQ
    RABBITMQ_URL: str

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Rate limiting (requests per minute)
    RATE_LIMIT_STARTER: int = 100
    RATE_LIMIT_GROWTH: int = 300
    RATE_LIMIT_ENTERPRISE: int = 1000

    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    # OpenAI (for knowledge base indexing)
    OPENAI_API_KEY: str

    # Feature flags
    ENABLE_RATE_LIMITING: bool = True
    ENABLE_WEBHOOKS: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
