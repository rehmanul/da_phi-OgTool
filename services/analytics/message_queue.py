"""
Redirect to shared internal queue for monolith deployment
"""
from services.shared.internal_queue import init_mq, publish_message, consume_messages, close_mq
