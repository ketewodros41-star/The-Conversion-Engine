"""
Tenacious Conversion Engine — SMS Handler
Secondary channel: Africa's Talking sandbox (free tier).
ONLY for warm leads who have replied by email and want scheduling via SMS.
LIVE_MODE=false routes to staff sink.
"""

import os
from datetime import datetime, timezone
from typing import Optional
import africastalking
import structlog

log = structlog.get_logger()

STAFF_SINK_NUMBER = os.getenv("STAFF_SINK_NUMBER", "+254700000000")
SENDER_ID = os.getenv("AT_SENDER_ID", "TENACIOUS")


class SMSHandler:
    """Africa's Talking SMS integration for warm-lead scheduling (secondary channel)."""

    def __init__(self, live_mode: bool = False):
        self.live_mode = live_mode
        africastalking.initialize(
            username=os.getenv("AT_USERNAME", "sandbox"),
            api_key=os.getenv("AT_API_KEY", "")
        )
        self.sms = africastalking.SMS

    def _get_recipient(self, to_number: str) -> str:
        if self.live_mode:
            return to_number
        log.debug("sms_routed_to_sink", original=to_number, sink=STAFF_SINK_NUMBER)
        return STAFF_SINK_NUMBER

    async def send_scheduling_sms(self, to_number: str, message: str) -> dict:
        """Send scheduling SMS to warm lead. Routes to sink unless LIVE_MODE=true."""
        recipient = self._get_recipient(to_number)
        prefix = "[SANDBOX] " if not self.live_mode else ""
        try:
            response = self.sms.send(
                message=f"{prefix}{message}",
                recipients=[recipient],
                sender_id=SENDER_ID,
            )
            log.info("sms_sent", to=recipient, live_mode=self.live_mode)
            return {"sent": True, "response": response}
        except Exception as e:
            log.error("sms_send_failed", error=str(e))
            return {"sent": False, "error": str(e)}

    async def handle_stop(self, from_number: str) -> None:
        """Process STOP command — mandatory compliance."""
        log.info("sms_stop_received", number=from_number)
        # Confirm opt-out
        try:
            self.sms.send(
                message="You've been unsubscribed. You will not receive further messages from Tenacious. Reply START to re-subscribe.",
                recipients=[self._get_recipient(from_number)],
                sender_id=SENDER_ID,
            )
        except Exception as e:
            log.error("stop_confirmation_failed", error=str(e))

    async def handle_scheduling_message(self, contact: dict, message: str,
                                         calendar) -> dict:
        """Parse scheduling intent from SMS and book a call if possible."""
        msg_lower = message.lower()

        # Parse slot preference from SMS
        if any(w in msg_lower for w in ["yes", "works", "good", "confirm", "book", "first", "option 1"]):
            slots = await calendar.get_available_slots(days_ahead=7)
            if slots:
                slot = slots[0]
                event = await calendar.book_slot(
                    slot_id=slot["id"],
                    attendee_email=contact.get("email"),
                    attendee_name=f"{contact.get('firstname', '')} {contact.get('lastname', '')}",
                    attendee_phone=contact.get("phone"),
                )
                # Confirm via SMS
                tz_label = _infer_timezone_label(contact)
                await self.send_scheduling_sms(
                    to_number=contact.get("phone", ""),
                    message=f"Confirmed! Your discovery call with Tenacious is scheduled for {slot['display']} {tz_label}. Check your email for the calendar invite.",
                )
                return {"booked": True, "call_time": slot["display"], "event_id": event.get("id")}

        # Prospect wants a different time
        elif any(w in msg_lower for w in ["other", "different", "can't", "what about", "how about"]):
            slots = await calendar.get_available_slots(days_ahead=14)
            slot_options = "\n".join([f"• {s['display']}" for s in slots[1:4]])
            await self.send_scheduling_sms(
                to_number=contact.get("phone", ""),
                message=f"No problem — here are a few more options:\n{slot_options}\nWhich works?",
            )
            return {"booked": False, "next_action": "waiting_for_slot_selection"}

        return {"booked": False, "next_action": "unrecognized_intent"}


def _infer_timezone_label(contact: dict) -> str:
    """Infer timezone from contact location for scheduling confirmation."""
    location = contact.get("city", "").lower() + contact.get("country", "").lower()
    if any(x in location for x in ["nairobi", "addis", "ethiopia", "kenya", "east africa"]):
        return "EAT"
    elif any(x in location for x in ["london", "berlin", "paris", "amsterdam", "europe"]):
        return "CET/BST"
    else:
        return "ET"  # Default to US Eastern for Tenacious primary market
