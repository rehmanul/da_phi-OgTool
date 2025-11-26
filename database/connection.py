"""
Database connection and session management
Production-ready PostgreSQL configuration
"""
import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import NullPool, QueuePool
from contextlib import contextmanager
import structlog

logger = structlog.get_logger()

# Database configuration
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://localhost/ogtool")

# Handle Render's DATABASE_URL format
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Production engine configuration
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=3600,  # Recycle connections after 1 hour
    echo=False,  # Set to True for debugging
    connect_args={
        "connect_timeout": 10,
        "options": "-c statement_timeout=30000"  # 30 seconds statement timeout
    }
)

# Session factory
SessionLocal = scoped_session(
    sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
        expire_on_commit=False
    )
)

@contextmanager
def get_db():
    """
    Provide a transactional scope for database operations.
    Automatically handles commit/rollback and session cleanup.
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database transaction failed: {e}")
        raise
    finally:
        session.close()

def init_database():
    """Initialize the database schema"""
    from database.models import Base
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database schema initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

def test_connection():
    """Test database connectivity"""
    try:
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            logger.info("Database connection successful")
            return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False

# Connection pool monitoring
@event.listens_for(engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    """Log new connections"""
    connection_record.info['pid'] = os.getpid()

@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_conn, connection_record, connection_proxy):
    """Verify connection on checkout"""
    pid = os.getpid()
    if connection_record.info['pid'] != pid:
        connection_record.connection = connection_proxy.connection = None
        raise Exception(f"Connection record belongs to pid {connection_record.info['pid']}, not {pid}")

# Async support for FastAPI
async def get_async_db():
    """Async database session for FastAPI endpoints"""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

def close_database():
    """Close all database connections"""
    SessionLocal.remove()
    engine.dispose()
    logger.info("Database connections closed")