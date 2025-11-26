"""RabbitMQ message queue integration"""
import json
import asyncio
from typing import Optional, Dict, Any, Callable
import aio_pika
import structlog

from app.config import settings

logger = structlog.get_logger()

_connection: Optional[aio_pika.Connection] = None
_channel: Optional[aio_pika.Channel] = None


async def init_mq():
    """Initialize RabbitMQ connection"""
    global _connection, _channel

    _connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
    _channel = await _connection.channel()
    await _channel.set_qos(prefetch_count=10)

    logger.info("Message queue initialized")


async def consume_messages(routing_key: str, callback: Callable):
    """Consume messages from queue"""
    if not _channel:
        await init_mq()

    queue = await _channel.declare_queue("analytics.events", durable=True)

    async def message_handler(message: aio_pika.IncomingMessage):
        async with message.process():
            try:
                data = json.loads(message.body.decode())
                await callback(data)
            except Exception as e:
                logger.error("Error processing message", error=str(e), exc_info=True)

    await queue.consume(message_handler)
    logger.info("Started consuming messages", routing_key=routing_key)

    # Keep consuming
    await asyncio.Future()


async def close_mq():
    """Close message queue connection"""
    global _connection, _channel

    if _channel:
        await _channel.close()

    if _connection:
        await _connection.close()

    logger.info("Message queue closed")
