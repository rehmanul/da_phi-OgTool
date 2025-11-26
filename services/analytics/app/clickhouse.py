"""ClickHouse connection management"""
from typing import Optional
from clickhouse_driver import Client
import structlog

from app.config import settings

logger = structlog.get_logger()

_client: Optional[Client] = None


async def init_clickhouse():
    """Initialize ClickHouse client"""
    global _client

    _client = Client(
        host=settings.CLICKHOUSE_HOST,
        port=settings.CLICKHOUSE_PORT,
        database=settings.CLICKHOUSE_DATABASE,
        user=settings.CLICKHOUSE_USER,
        password=settings.CLICKHOUSE_PASSWORD,
    )

    logger.info("ClickHouse client initialized")


async def get_clickhouse_client() -> Client:
    """Get ClickHouse client"""
    if _client is None:
        await init_clickhouse()
    return _client


async def close_clickhouse():
    """Close ClickHouse client"""
    global _client
    if _client:
        _client.disconnect()
        logger.info("ClickHouse client closed")
