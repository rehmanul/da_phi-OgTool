"""
Analytics Service - Production Implementation
Processes analytics data and calculates metrics
"""
import asyncio
import signal
import sys
from typing import Optional
import structlog

from app.config import settings
from app.analytics_engine import AnalyticsEngine
from app.database import init_db, close_db
from app.clickhouse import init_clickhouse, close_clickhouse
from app.message_queue import init_mq, close_mq, consume_messages
from app.metrics import start_metrics_server

logger = structlog.get_logger()


class AnalyticsService:
    """Main service orchestrator for analytics processing"""

    def __init__(self):
        self.engine: Optional[AnalyticsEngine] = None
        self.running = False

    async def start(self):
        """Initialize and start the analytics service"""
        logger.info("Starting Analytics Service", version=settings.VERSION)

        # Initialize databases
        await init_db()
        logger.info("PostgreSQL initialized")

        await init_clickhouse()
        logger.info("ClickHouse initialized")

        # Initialize message queue
        await init_mq()
        logger.info("Message queue initialized")

        # Start metrics server
        start_metrics_server(port=9095)
        logger.info("Metrics server started", port=9095)

        # Initialize analytics engine
        self.engine = AnalyticsEngine()
        await self.engine.initialize()
        logger.info("Analytics engine initialized")

        # Start periodic aggregations
        self.running = True
        asyncio.create_task(self.engine.run_periodic_aggregations())

        # Start consuming analytics events
        await consume_messages("analytics.*", self.process_analytics_event)

    async def process_analytics_event(self, message: dict):
        """Process analytics event from message queue"""
        try:
            await self.engine.process_event(message)
        except Exception as e:
            logger.error("Error processing analytics event", error=str(e), exc_info=True)

    async def stop(self):
        """Gracefully shutdown the service"""
        logger.info("Shutting down Analytics Service")
        self.running = False

        if self.engine:
            await self.engine.stop()

        await close_clickhouse()
        await close_mq()
        await close_db()

        logger.info("Service shutdown complete")

    def handle_signal(self, sig, frame):
        """Handle shutdown signals"""
        logger.info("Received shutdown signal", signal=sig)
        asyncio.create_task(self.stop())


async def main():
    """Main entry point"""
    service = AnalyticsService()

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
