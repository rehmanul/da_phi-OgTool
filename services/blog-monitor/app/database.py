"""Database connection management"""
import asyncpg
from typing import Optional
import structlog

from app.config import settings

logger = structlog.get_logger()

_pool: Optional[asyncpg.Pool] = None


async def init_db():
    """Initialize database connection pool"""
    global _pool

    _pool = await asyncpg.create_pool(
        settings.DATABASE_URL,
        min_size=5,
        max_size=settings.DB_POOL_SIZE,
        max_inactive_connection_lifetime=300,
        command_timeout=60,
    )

    logger.info("Database pool created", pool_size=settings.DB_POOL_SIZE)


async def get_db_pool() -> asyncpg.Pool:
    """Get database connection pool"""
    if _pool is None:
        await init_db()
    return _pool


async def close_db():
    """Close database connection pool"""
    global _pool
    if _pool:
        await _pool.close()
        logger.info("Database pool closed")
