"""
Webhook Dispatcher for Integrations
Supports Zapier, N8N, Make, and custom webhooks
"""
import asyncio
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import httpx
import structlog
from database.models import Lead, Alert, WebhookLog, WebhookEvent

logger = structlog.get_logger()

class WebhookDispatcher:
    """Production webhook dispatcher with retry logic"""

    def __init__(self):
        """Initialize webhook dispatcher"""
        self.client = httpx.AsyncClient(timeout=30.0)
        self.retry_delays = [1, 5, 15]  # Seconds between retries

    async def send_leads(self, webhook_url: str, leads: List[Lead]) -> bool:
        """Send leads to webhook endpoint"""
        payload = {
            "event": "leads_found",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "count": len(leads),
                "leads": [self._serialize_lead(lead) for lead in leads]
            }
        }

        return await self._send_webhook(webhook_url, payload, WebhookEvent.LEAD_FOUND)

    async def send_alert(self, webhook_url: str, alert: Alert) -> bool:
        """Send alert to webhook endpoint"""
        payload = {
            "event": "monitor_alert",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "type": alert.type,
                "severity": alert.severity,
                "title": alert.title,
                "message": alert.message,
                "alert_data": alert.data
            }
        }

        return await self._send_webhook(webhook_url, payload, WebhookEvent.MONITOR_ALERT)

    async def send_response_generated(
        self,
        webhook_url: str,
        lead: Lead,
        response_content: str,
        persona_name: str
    ) -> bool:
        """Send notification when AI response is generated"""
        payload = {
            "event": "response_generated",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "lead": self._serialize_lead(lead),
                "response": {
                    "content": response_content,
                    "persona": persona_name,
                    "generated_at": datetime.utcnow().isoformat()
                }
            }
        }

        return await self._send_webhook(webhook_url, payload, WebhookEvent.RESPONSE_GENERATED)

    async def send_zapier_trigger(self, webhook_url: str, data: Dict[str, Any]) -> bool:
        """Send Zapier-formatted webhook"""
        # Zapier expects flat structure for easier mapping
        flat_data = self._flatten_dict(data)

        return await self._send_webhook(
            webhook_url,
            flat_data,
            WebhookEvent.LEAD_FOUND,
            headers={"X-Hook-Source": "OGTool"}
        )

    async def send_n8n_webhook(self, webhook_url: str, data: Dict[str, Any]) -> bool:
        """Send N8N-formatted webhook"""
        # N8N can handle nested structures
        payload = {
            "source": "ogtool",
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }

        return await self._send_webhook(
            webhook_url,
            payload,
            WebhookEvent.LEAD_FOUND
        )

    async def send_make_webhook(self, webhook_url: str, data: Dict[str, Any]) -> bool:
        """Send Make (Integromat) formatted webhook"""
        # Make prefers simple structure
        payload = {
            "app": "ogtool",
            "event_type": data.get("event", "lead_found"),
            "occurred_at": datetime.utcnow().isoformat(),
            **data
        }

        return await self._send_webhook(
            webhook_url,
            payload,
            WebhookEvent.LEAD_FOUND
        )

    async def _send_webhook(
        self,
        url: str,
        payload: Dict[str, Any],
        event_type: WebhookEvent,
        headers: Optional[Dict[str, str]] = None,
        webhook_id: Optional[int] = None
    ) -> bool:
        """Send webhook with retry logic"""
        default_headers = {
            "Content-Type": "application/json",
            "User-Agent": "OGTool/2.0 Webhook",
            "X-OGTool-Event": event_type.value
        }

        if headers:
            default_headers.update(headers)

        # Attempt to send with retries
        for attempt, delay in enumerate(self.retry_delays + [None]):
            try:
                response = await self.client.post(
                    url,
                    json=payload,
                    headers=default_headers
                )

                # Log webhook attempt
                if webhook_id:
                    await self._log_webhook(
                        webhook_id,
                        event_type,
                        payload,
                        response.status_code,
                        response.text
                    )

                if response.status_code in [200, 201, 202, 204]:
                    logger.info(f"Webhook sent successfully to {url}")
                    return True
                elif response.status_code >= 500:
                    # Server error, retry
                    if delay:
                        logger.warning(f"Webhook server error ({response.status_code}), retrying in {delay}s")
                        await asyncio.sleep(delay)
                        continue
                else:
                    # Client error, don't retry
                    logger.error(f"Webhook client error ({response.status_code}): {response.text}")
                    return False

            except httpx.TimeoutException:
                logger.error(f"Webhook timeout for {url}")
                if delay:
                    await asyncio.sleep(delay)
                    continue
            except Exception as e:
                logger.error(f"Webhook error: {e}")
                if delay:
                    await asyncio.sleep(delay)
                    continue

        logger.error(f"Webhook failed after all retries: {url}")
        return False

    def _serialize_lead(self, lead: Lead) -> Dict[str, Any]:
        """Serialize lead for webhook payload"""
        return {
            "id": lead.id,
            "platform": lead.platform.value if hasattr(lead.platform, 'value') else str(lead.platform),
            "title": lead.title,
            "content": lead.content[:500],  # Truncate for webhooks
            "author": lead.author,
            "url": lead.url,
            "scores": {
                "relevance": lead.relevance_score,
                "engagement": lead.engagement_score,
                "opportunity": lead.opportunity_score,
                "total": lead.total_score
            },
            "metadata": {
                "subreddit": lead.subreddit,
                "karma": lead.post_karma,
                "comments": lead.comment_count,
                "intent": lead.ai_intent,
                "sentiment": lead.ai_sentiment
            },
            "found_at": lead.found_at.isoformat() if lead.found_at else None,
            "posted_at": lead.posted_at.isoformat() if lead.posted_at else None
        }

    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = '', sep: str = '_') -> Dict[str, Any]:
        """Flatten nested dictionary for Zapier"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                # Convert lists to comma-separated strings for Zapier
                items.append((new_key, ', '.join(str(i) for i in v)))
            else:
                items.append((new_key, v))
        return dict(items)

    async def _log_webhook(
        self,
        webhook_id: int,
        event: WebhookEvent,
        payload: Dict[str, Any],
        response_status: int,
        response_body: str,
        error_message: Optional[str] = None
    ):
        """Log webhook attempt to database"""
        from database.connection import get_db

        try:
            with get_db() as db:
                log = WebhookLog(
                    webhook_id=webhook_id,
                    event=event,
                    payload=payload,
                    response_status=response_status,
                    response_body=response_body[:1000] if response_body else None,
                    error_message=error_message
                )
                db.add(log)
                db.commit()
        except Exception as e:
            logger.error(f"Failed to log webhook: {e}")

    async def test_webhook(self, url: str) -> Dict[str, Any]:
        """Test webhook connectivity"""
        test_payload = {
            "test": True,
            "timestamp": datetime.utcnow().isoformat(),
            "message": "OGTool webhook test"
        }

        try:
            response = await self.client.post(
                url,
                json=test_payload,
                headers={
                    "Content-Type": "application/json",
                    "X-OGTool-Test": "true"
                },
                timeout=10.0
            )

            return {
                "success": response.status_code in [200, 201, 202, 204],
                "status_code": response.status_code,
                "response": response.text[:500] if response.text else None
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

# Webhook templates for popular services
WEBHOOK_TEMPLATES = {
    "zapier": {
        "name": "Zapier",
        "url_pattern": "https://hooks.zapier.com/hooks/catch/",
        "format": "flat",
        "documentation": "https://zapier.com/help/create/code-webhooks/trigger-zaps-from-webhooks"
    },
    "n8n": {
        "name": "N8N",
        "url_pattern": "webhook.n8n.io",
        "format": "nested",
        "documentation": "https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.webhook/"
    },
    "make": {
        "name": "Make (Integromat)",
        "url_pattern": "hook.integromat.com",
        "format": "simple",
        "documentation": "https://www.make.com/en/help/tools/webhooks"
    },
    "pabbly": {
        "name": "Pabbly Connect",
        "url_pattern": "connect.pabbly.com/workflow/sendwebhookdata/",
        "format": "nested",
        "documentation": "https://www.pabbly.com/connect/webhook/"
    },
    "microsoft_power_automate": {
        "name": "Microsoft Power Automate",
        "url_pattern": "prod-",
        "format": "nested",
        "documentation": "https://docs.microsoft.com/en-us/power-automate/triggers-introduction"
    },
    "slack": {
        "name": "Slack",
        "url_pattern": "hooks.slack.com/services/",
        "format": "slack",
        "documentation": "https://api.slack.com/messaging/webhooks"
    }
}