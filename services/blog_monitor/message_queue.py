"""RabbitMQ message queue integration"""
import json
import aio_pika
from typing import Optional, Dict, Any
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

    logger.info("Message queue initialized")


async def publish_message(queue: str, message: Dict[str, Any]):
    """Publish message to queue"""
    if not _channel:
        await init_mq()

    exchange = await _channel.get_exchange("ogtool")

    await exchange.publish(
        aio_pika.Message(
            body=json.dumps(message).encode(),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        ),
        routing_key=queue,
    )


async def close_mq():
    """Close message queue connection"""
    global _connection, _channel

    if _channel:
        await _channel.close()

    if _connection:
        await _connection.close()

    logger.info("Message queue closed")
