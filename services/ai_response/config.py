"""Configuration management for AI Response Service"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""

    # Service info
    VERSION: str = "1.0.0"
    SERVICE_NAME: str = "ai-response"

    # Database
    DATABASE_URL: str
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 40

    # Redis
    REDIS_URL: str
    REDIS_MAX_CONNECTIONS: int = 50

    # RabbitMQ
    RABBITMQ_URL: str

    # Qdrant Vector Store
    QDRANT_URL: str = "http://qdrant:6333"
    QDRANT_COLLECTION: str = "knowledge_base"

    # Perplexity (Primary)
    PERPLEXITY_API_KEY: str
    PERPLEXITY_MODEL: str = "llama-3.1-sonar-small-128k-online"

    # Google Gemini (Fallback)
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-1.5-flash"

    # Legacy/Optional (OpenAI/Anthropic)
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-large"

    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL: str = "claude-3-opus-20240229"

    # Generation parameters
    DEFAULT_TEMPERATURE: float = 0.7
    DEFAULT_MAX_TOKENS: int = 500
    MAX_CONTEXT_LENGTH: int = 8000

    # Quality thresholds
    MIN_QUALITY_SCORE: float = 0.6
    AUTO_APPROVE_THRESHOLD: float = 0.8
    MIN_SAFETY_SCORE: float = 0.7

    # Cost limits (per response)
    MAX_COST_PER_RESPONSE: float = 0.50

    # Retry configuration
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 2

    # Feature flags
    ENABLE_CONTENT_MODERATION: bool = True
    ENABLE_QUALITY_SCORING: bool = True
    ENABLE_COST_TRACKING: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
