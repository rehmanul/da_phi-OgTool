"""
AI Response Generation Service - Production Implementation
Generates context-aware responses using LLMs with persona and knowledge base integration
"""
import asyncio
import signal
import sys
from typing import Optional
import structlog

from app.config import settings
from app.response_generator import ResponseGenerator
from app.database import init_db, close_db
from app.message_queue import init_mq, close_mq, consume_messages
from app.vector_store import init_vector_store, close_vector_store
from app.metrics import start_metrics_server

logger = structlog.get_logger()


class AIResponseService:
    """Main service orchestrator for AI response generation"""

    def __init__(self):
        self.generator: Optional[ResponseGenerator] = None
        self.running = False

    async def start(self):
        """Initialize and start the service"""
        logger.info("Starting AI Response Service", version=settings.VERSION)

        # Initialize database
        await init_db()
        logger.info("Database initialized")

        # Initialize vector store
        await init_vector_store()
        logger.info("Vector store initialized")

        # Initialize message queue
        await init_mq()
        logger.info("Message queue initialized")

        # Start metrics server
        start_metrics_server(port=9092)
        logger.info("Metrics server started", port=9092)

        # Initialize response generator
        self.generator = ResponseGenerator()
        await self.generator.initialize()
        logger.info("Response generator initialized")

        # Start consuming messages
        self.running = True
        await self.consume_post_detection_events()

    async def consume_post_detection_events(self):
        """Consume post detection events and generate responses"""
        async def callback(message):
            try:
                await self.generator.process_detected_post(message)
            except Exception as e:
                logger.error("Error processing message", error=str(e), exc_info=True)

        await consume_messages("post.detected", callback)

    async def stop(self):
        """Gracefully shutdown the service"""
        logger.info("Shutting down AI Response Service")
        self.running = False

        if self.generator:
            await self.generator.close()

        await close_vector_store()
        await close_mq()
        await close_db()

        logger.info("Service shutdown complete")

    def handle_signal(self, sig, frame):
        """Handle shutdown signals"""
        logger.info("Received shutdown signal", signal=sig)
        asyncio.create_task(self.stop())


async def main():
    """Main entry point"""
    service = AIResponseService()

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
