"""ClickHouse connection management"""
from typing import Optional, Any
import structlog

from app.config import settings

logger = structlog.get_logger()

# Optional ClickHouse support
try:
    from clickhouse_driver import Client
    HAS_CLICKHOUSE = True
except ImportError:
    HAS_CLICKHOUSE = False
    Client = None

_client: Optional[Any] = None


async def init_clickhouse():
    """Initialize ClickHouse client"""
    global _client

    if not HAS_CLICKHOUSE:
        logger.warning("ClickHouse driver not available, skipping initialization")
        return

    # Skip if host is not configured or explicitly disabled
    if not settings.CLICKHOUSE_HOST or settings.CLICKHOUSE_HOST == "disabled":
        logger.info("ClickHouse disabled by configuration")
        return

    try:
        _client = Client(
            host=settings.CLICKHOUSE_HOST,
            port=settings.CLICKHOUSE_PORT,
            database=settings.CLICKHOUSE_DATABASE,
            user=settings.CLICKHOUSE_USER,
            password=settings.CLICKHOUSE_PASSWORD,
        )
        logger.info("ClickHouse client initialized")
    except Exception as e:
        logger.warning("Failed to initialize ClickHouse, continuing without analytics storage", error=str(e))
        _client = None


async def get_clickhouse_client() -> Optional[Any]:
    """Get ClickHouse client"""
    if _client is None:
        await init_clickhouse()
    return _client


async def close_clickhouse():
    """Close ClickHouse client"""
    global _client
    if _client:
        try:
            _client.disconnect()
            logger.info("ClickHouse client closed")
        except Exception:
            pass

