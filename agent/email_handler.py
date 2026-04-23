"""
Tenacious Conversion Engine - Email Handler
Primary outreach channel: Resend (free tier, 3,000 emails/month).
LIVE_MODE=false routes all outbound to staff sink (default).
"""

import os
from typing import Optional

import resend
import structlog

from event_bus import EventBus

log = structlog.get_logger()

STAFF_SINK_EMAIL = os.getenv("STAFF_SINK_EMAIL", "sink@tenacious-challenge.example.com")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "outreach@tenacious.example.com")
SENDER_NAME = "Tenacious Consulting"


class EmailHandler:
    """Manages outbound email, inbound reply events, and bounce events."""

    def __init__(self, live_mode: bool = False, event_bus: Optional[EventBus] = None):
        self.live_mode = live_mode
        self.event_bus = event_bus or EventBus()
        resend.api_key = os.getenv("RESEND_API_KEY")
        if not resend.api_key:
            log.warning("resend_api_key_missing", msg="Set RESEND_API_KEY in .env")

    def on_reply(self, handler) -> None:
        self.event_bus.subscribe("email.reply.received", handler)

    def on_bounce(self, handler) -> None:
        self.event_bus.subscribe("email.bounce.received", handler)

    def on_send_failure(self, handler) -> None:
        self.event_bus.subscribe("email.send.failed", handler)

    def _get_recipient(self, to_email: str) -> str:
        if self.live_mode:
            return to_email
        log.debug("email_routed_to_sink", original=to_email, sink=STAFF_SINK_EMAIL)
        return STAFF_SINK_EMAIL

    async def send_outbound(
        self,
        to_email: str,
        subject: str,
        body: str,
        metadata: Optional[dict] = None,
    ) -> dict:
        recipient = self._get_recipient(to_email)
        if not self.live_mode:
            subject = f"[SANDBOX] {subject}"

        try:
            result = resend.Emails.send({
                "from": f"{SENDER_NAME} <{SENDER_EMAIL}>",
                "to": [recipient],
                "subject": subject,
                "text": body,
                "tags": [
                    {"name": "is_draft", "value": "true"},
                    {"name": "live_mode", "value": str(self.live_mode).lower()},
                    {
                        "name": "crunchbase_id",
                        "value": metadata.get("crunchbase_id", "unknown") if metadata else "unknown",
                    },
                ],
            })
            log.info(
                "email_sent",
                to=recipient,
                original_to=to_email if not self.live_mode else None,
                live_mode=self.live_mode,
                message_id=result.get("id"),
            )
            return {"sent": True, "message_id": result.get("id"), "recipient": recipient}
        except Exception as exc:
            log.error("email_send_failed", error=str(exc), to=to_email)
            await self.event_bus.emit("email.send.failed", {
                "to_email": to_email,
                "subject": subject,
                "metadata": metadata or {},
                "error": str(exc),
            })
            return {"sent": False, "error": str(exc)}

    async def send_reply(
        self,
        to_email: str,
        subject: str,
        body: str,
        in_reply_to: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> dict:
        recipient = self._get_recipient(to_email)
        params = {
            "from": f"{SENDER_NAME} <{SENDER_EMAIL}>",
            "to": [recipient],
            "subject": subject,
            "text": body,
        }
        if in_reply_to:
            params["headers"] = {"In-Reply-To": in_reply_to, "References": in_reply_to}

        try:
            result = resend.Emails.send(params)
            log.info("email_reply_sent", to=recipient, subject=subject)
            return {"sent": True, "message_id": result.get("id")}
        except Exception as exc:
            log.error("email_reply_failed", error=str(exc), to=to_email)
            await self.event_bus.emit("email.send.failed", {
                "to_email": to_email,
                "subject": subject,
                "metadata": metadata or {},
                "error": str(exc),
                "kind": "reply",
            })
            return {"sent": False, "error": str(exc)}

    async def process_inbound_reply(self, payload: dict) -> dict:
        """Expose inbound email replies to downstream consumers via event emission."""
        event = {
            "channel": "email",
            "from_email": payload["from_email"],
            "subject": payload["subject"],
            "body": payload["body"],
            "message_id": payload["message_id"],
            "in_reply_to": payload.get("in_reply_to"),
        }
        await self.event_bus.emit("email.reply.received", event)
        return event

    async def process_bounce_event(self, payload: dict) -> dict:
        """Handle bounce payloads without dead-ending or silent failure."""
        event = {
            "channel": "email",
            "event_type": payload.get("event_type", "bounce"),
            "recipient": payload["recipient"],
            "message_id": payload.get("message_id"),
            "reason": payload.get("reason", "unknown"),
            "raw": payload,
        }
        await self.event_bus.emit("email.bounce.received", event)
        return event
