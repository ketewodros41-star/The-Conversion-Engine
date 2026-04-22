"""
Tenacious Conversion Engine — Email Handler
Primary outreach channel: Resend (free tier, 3,000 emails/month).
LIVE_MODE=false routes all outbound to staff sink (default).
"""

import os
from typing import Optional
import resend
import structlog

log = structlog.get_logger()

STAFF_SINK_EMAIL = os.getenv("STAFF_SINK_EMAIL", "sink@tenacious-challenge.example.com")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "outreach@tenacious.example.com")
SENDER_NAME = "Tenacious Consulting"


class EmailHandler:
    """Manages outbound email via Resend and inbound reply webhook."""

    def __init__(self, live_mode: bool = False):
        self.live_mode = live_mode
        resend.api_key = os.getenv("RESEND_API_KEY")
        if not resend.api_key:
            log.warning("resend_api_key_missing", msg="Set RESEND_API_KEY in .env")

    def _get_recipient(self, to_email: str) -> str:
        """Route to staff sink unless LIVE_MODE=true (kill-switch default)."""
        if self.live_mode:
            return to_email
        log.debug("email_routed_to_sink", original=to_email, sink=STAFF_SINK_EMAIL)
        return STAFF_SINK_EMAIL

    async def send_outbound(self, to_email: str, subject: str, body: str,
                             metadata: Optional[dict] = None) -> dict:
        """Send outbound email. Routes to staff sink by default."""
        recipient = self._get_recipient(to_email)

        # Prefix subject with [DRAFT] if not live mode
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
                    {"name": "live_mode", "value": str(self.live_mode)},
                    {"name": "crunchbase_id",
                     "value": metadata.get("crunchbase_id", "unknown") if metadata else "unknown"},
                ],
            })
            log.info("email_sent",
                     to=recipient,
                     original_to=to_email if not self.live_mode else None,
                     live_mode=self.live_mode,
                     message_id=result.get("id"))
            return {"sent": True, "message_id": result.get("id"), "recipient": recipient}

        except Exception as e:
            log.error("email_send_failed", error=str(e), to=to_email)
            return {"sent": False, "error": str(e)}

    async def send_reply(self, to_email: str, subject: str, body: str,
                          in_reply_to: Optional[str] = None,
                          metadata: Optional[dict] = None) -> dict:
        """Send reply to an inbound email."""
        recipient = self._get_recipient(to_email)
        try:
            params = {
                "from": f"{SENDER_NAME} <{SENDER_EMAIL}>",
                "to": [recipient],
                "subject": subject,
                "text": body,
            }
            if in_reply_to:
                params["reply_to"] = in_reply_to

            result = resend.Emails.send(params)
            log.info("email_reply_sent", to=recipient, subject=subject)
            return {"sent": True, "message_id": result.get("id")}
        except Exception as e:
            log.error("email_reply_failed", error=str(e))
            return {"sent": False, "error": str(e)}
