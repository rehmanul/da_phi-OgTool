"""
Reddit Monitor Service - Production Implementation
Monitors Reddit for relevant posts and comments based on keywords and subreddits
"""
import asyncio
import signal
import sys
from typing import Optional
import structlog

from app.config import settings
from app.reddit_client import RedditMonitor
from app.database import init_db, close_db
from app.message_queue import init_mq, close_mq
from app.metrics import start_metrics_server

logger = structlog.get_logger()


class RedditMonitorService:
    """Main service orchestrator for Reddit monitoring"""

    def __init__(self):
        self.monitor: Optional[RedditMonitor] = None
        self.running = False

    async def start(self):
        """Initialize and start the monitoring service"""
        logger.info("Starting Reddit Monitor Service", version=settings.VERSION)

        # Initialize database connection
        await init_db()
        logger.info("Database initialized")

        # Initialize message queue
        await init_mq()
        logger.info("Message queue initialized")

        # Start Prometheus metrics server
        start_metrics_server(port=9091)
        logger.info("Metrics server started", port=9091)

        # Initialize Reddit monitor
        self.monitor = RedditMonitor()
        await self.monitor.initialize()
        logger.info("Reddit monitor initialized")

        # Start monitoring
        self.running = True
        await self.monitor.start_monitoring()

    async def stop(self):
        """Gracefully shutdown the service"""
        logger.info("Shutting down Reddit Monitor Service")
        self.running = False

        if self.monitor:
            await self.monitor.stop()

        await close_mq()
        await close_db()

        logger.info("Service shutdown complete")

    def handle_signal(self, sig, frame):
        """Handle shutdown signals"""
        logger.info("Received shutdown signal", signal=sig)
        asyncio.create_task(self.stop())


async def main():
    """Main entry point"""
    service = RedditMonitorService()

    # Register signal handlers
    signal.signal(signal.SIGINT, service.handle_signal)
    signal.signal(signal.SIGTERM, service.handle_signal)

    try:
        await service.start()
    except Exception as e:
        logger.error("Service error", error=str(e), exc_info=True)
        await service.stop()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
