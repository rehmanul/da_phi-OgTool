"""
Internal in-memory message queue to replace RabbitMQ for 0-cost deployment.
"""
import asyncio
import json
import structlog
from typing import Dict, Any, Callable, List, Set

logger = structlog.get_logger()

class InternalQueue:
    def __init__(self):
        self.queues: Dict[str, asyncio.Queue] = {}
        self.subscribers: Dict[str, List[Callable]] = {}
        self.running = False

    async def initialize(self):
        self.running = True
        logger.info("Internal in-memory queue initialized")

    async def publish(self, queue_name: str, message: Dict[str, Any]):
        """Publish message to a queue (and notify subscribers directly)"""
        if queue_name not in self.queues:
            self.queues[queue_name] = asyncio.Queue()
        
        # Add to queue for consumers
        await self.queues[queue_name].put(message)
        
        # Also notify any direct subscribers (pub/sub pattern)
        if queue_name in self.subscribers:
            for callback in self.subscribers[queue_name]:
                try:
                    await callback(message)
                except Exception as e:
                    logger.error("Error in subscriber callback", queue=queue_name, error=str(e))
        
        logger.debug("Message published to internal queue", queue=queue_name)

    async def subscribe(self, queue_name: str, callback: Callable):
        """Subscribe to a queue (pub/sub style)"""
        if queue_name not in self.subscribers:
            self.subscribers[queue_name] = []
        self.subscribers[queue_name].append(callback)
        logger.info("Subscribed to internal queue", queue=queue_name)

    async def consume(self, queue_name: str, callback: Callable):
        """Consume messages from a queue (worker style)"""
        if queue_name not in self.queues:
            self.queues[queue_name] = asyncio.Queue()
            
        logger.info("Starting consumer for internal queue", queue=queue_name)
        
        while self.running:
            try:
                message = await self.queues[queue_name].get()
                try:
                    await callback(message)
                except Exception as e:
                    logger.error("Error processing message", queue=queue_name, error=str(e))
                finally:
                    self.queues[queue_name].task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in consumer loop", queue=queue_name, error=str(e))
                await asyncio.sleep(1)

    async def close(self):
        self.running = False
        logger.info("Internal queue closed")

# Global instance
internal_queue = InternalQueue()

# Compatibility wrappers
async def init_mq():
    await internal_queue.initialize()

async def publish_message(queue: str, message: Dict[str, Any]):
    await internal_queue.publish(queue, message)

async def consume_messages(queue_name: str, callback: Callable):
    # Start consumer in background task
    asyncio.create_task(internal_queue.consume(queue_name, callback))

async def close_mq():
    await internal_queue.close()
