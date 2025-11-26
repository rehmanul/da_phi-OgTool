"""Configuration management"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    # Service info
    VERSION: str = "1.0.0"
    SERVICE_NAME: str = "analytics"

    # PostgreSQL
    DATABASE_URL: str
    DB_POOL_SIZE: int = 20

    # ClickHouse
    CLICKHOUSE_HOST: str = "clickhouse"
    CLICKHOUSE_PORT: int = 9000
    CLICKHOUSE_DATABASE: str = "ogtool"
    CLICKHOUSE_USER: str = "default"
    CLICKHOUSE_PASSWORD: str = ""

    # Redis
    REDIS_URL: str

    # RabbitMQ
    RABBITMQ_URL: str

    # Aggregation intervals (seconds)
    HOURLY_AGGREGATION_INTERVAL: int = 3600
    DAILY_AGGREGATION_INTERVAL: int = 86400

    # Feature flags
    ENABLE_REALTIME_ANALYTICS: bool = True
    ENABLE_AGGREGATIONS: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
