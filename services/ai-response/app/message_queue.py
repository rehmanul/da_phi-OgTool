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

    logger.debug("Message published", queue=queue)


async def consume_messages(queue_name: str, callback: Callable):
    """Consume messages from queue"""
    if not _channel:
        await init_mq()

    queue = await _channel.get_queue(queue_name)

    async def message_handler(message: aio_pika.IncomingMessage):
        async with message.process():
            try:
                data = json.loads(message.body.decode())
                await callback(data)
            except Exception as e:
                logger.error("Error processing message", error=str(e), exc_info=True)
                # Message will be requeued due to exception

    await queue.consume(message_handler)
    logger.info("Started consuming messages", queue=queue_name)

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
