"""
Blog Monitor Service - Production Implementation
Monitors blogs via RSS feeds and web scraping
"""
import asyncio
import signal
import sys
from typing import Optional
import structlog

from app.config import settings
from app.blog_crawler import BlogMonitor
from app.database import init_db, close_db
from app.message_queue import init_mq, close_mq
from app.metrics import start_metrics_server

logger = structlog.get_logger()


class BlogMonitorService:
    """Main service orchestrator for blog monitoring"""

    def __init__(self):
        self.monitor: Optional[BlogMonitor] = None
        self.running = False

    async def start(self):
        """Initialize and start the monitoring service"""
        logger.info("Starting Blog Monitor Service", version=settings.VERSION)

        # Initialize database connection
        await init_db()
        logger.info("Database initialized")

        # Initialize message queue
        await init_mq()
        logger.info("Message queue initialized")

        # Start Prometheus metrics server
        start_metrics_server(port=9094)
        logger.info("Metrics server started", port=9094)

        # Initialize blog monitor
        self.monitor = BlogMonitor()
        await self.monitor.initialize()
        logger.info("Blog monitor initialized")

        # Start monitoring
        self.running = True
        await self.monitor.start_monitoring()

    async def stop(self):
        """Gracefully shutdown the service"""
        logger.info("Shutting down Blog Monitor Service")
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
    service = BlogMonitorService()

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
