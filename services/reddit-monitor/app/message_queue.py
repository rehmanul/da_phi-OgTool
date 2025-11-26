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

    # Declare exchanges and queues
    await setup_queues()

    logger.info("Message queue initialized")


async def setup_queues():
    """Setup exchanges and queues"""
    exchange = await _channel.declare_exchange(
        "ogtool", aio_pika.ExchangeType.TOPIC, durable=True
    )

    # Post detected queue
    post_queue = await _channel.declare_queue("post.detected", durable=True)
    await post_queue.bind(exchange, "post.detected")

    # Response generated queue
    response_queue = await _channel.declare_queue("response.generated", durable=True)
    await response_queue.bind(exchange, "response.generated")

    # Analytics queue
    analytics_queue = await _channel.declare_queue("analytics.event", durable=True)
    await analytics_queue.bind(exchange, "analytics.*")

    logger.info("Queues configured")


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
