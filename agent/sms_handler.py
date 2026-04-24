"""
Tenacious Conversion Engine - SMS Handler
Secondary channel: Africa's Talking sandbox (free tier).
Only for warm leads who have replied by email and want scheduling via SMS.
LIVE_MODE=false routes to staff sink.
"""

import os
from typing import Optional

import africastalking
import structlog

from event_bus import EventBus

log = structlog.get_logger()

STAFF_SINK_NUMBER = os.getenv("STAFF_SINK_NUMBER", "+254700000000")
SENDER_ID = os.getenv("AT_SENDER_ID", "TENACIOUS")


class SMSHandler:
    """Africa's Talking SMS integration for warm-lead scheduling."""

    def __init__(self, live_mode: bool = False, event_bus: Optional[EventBus] = None):
        self.live_mode = live_mode
        self.event_bus = event_bus or EventBus()
        africastalking.initialize(
            username=os.getenv("AT_USERNAME", "sandbox"),
            api_key=os.getenv("AT_API_KEY", ""),
        )
        self.sms = africastalking.SMS

    def on_inbound_message(self, handler) -> None:
        self.event_bus.subscribe("sms.inbound.received", handler)

    def on_stop(self, handler) -> None:
        self.event_bus.subscribe("sms.stop.received", handler)

    def on_booking_completed(self, handler) -> None:
        self.event_bus.subscribe("sms.booking.completed", handler)

    def _get_recipient(self, to_number: str) -> str:
        if self.live_mode:
            return to_number
        log.debug("sms_routed_to_sink", original=to_number, sink=STAFF_SINK_NUMBER)
        return STAFF_SINK_NUMBER

    async def send_scheduling_sms(self, to_number: str, message: str) -> dict:
        """Send scheduling SMS to a warm lead only."""
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
        except Exception as exc:
            log.error("sms_send_failed", error=str(exc), to=to_number)
            return {"sent": False, "error": str(exc)}

    async def handle_stop(self, from_number: str) -> None:
        """Process STOP command and emit downstream event."""
        log.info("sms_stop_received", number=from_number)
        await self.event_bus.emit("sms.stop.received", {
            "channel": "sms",
            "from_number": from_number,
            "command": "STOP",
        })
        try:
            self.sms.send(
                message=(
                    "You've been unsubscribed. You will not receive further messages "
                    "from Tenacious. Reply START to re-subscribe."
                ),
                recipients=[self._get_recipient(from_number)],
                sender_id=SENDER_ID,
            )
        except Exception as exc:
            log.error("stop_confirmation_failed", error=str(exc), number=from_number)

    async def handle_scheduling_message(self, contact: dict, message: str, calendar) -> dict:
        """Route inbound SMS into the scheduling flow for a warm lead."""
        msg_lower = message.lower()
        await self.event_bus.emit("sms.inbound.received", {
            "channel": "sms",
            "contact": contact,
            "message": message,
        })

        affirmative = ["yes", "works", "good", "confirm", "book", "first", "option 1"]
        alternate = ["other", "different", "can't", "what about", "how about"]

        if any(token in msg_lower for token in affirmative):
            slots = await calendar.get_available_slots(days_ahead=7)
            if slots:
                slot = slots[0]
                event = await calendar.book_slot(
                    slot_id=slot["id"],
                    attendee_email=contact.get("email", ""),
                    attendee_name=f"{contact.get('firstname', '')} {contact.get('lastname', '')}".strip(),
                    attendee_phone=contact.get("phone"),
                )
                await self.send_scheduling_sms(
                    to_number=contact.get("phone", ""),
                    message=(
                        f"Confirmed. Your discovery call with Tenacious is scheduled for "
                        f"{slot['display']} {_infer_timezone_label(contact)}. "
                        "Check your email for the calendar invite."
                    ),
                )
                result = {"booked": True, "call_time": slot["display"], "event_id": event.get("id")}
                await self.event_bus.emit("sms.booking.completed", {
                    "channel": "sms",
                    "contact": contact,
                    "booking": result,
                })
                return result

        if any(token in msg_lower for token in alternate):
            slots = await calendar.get_available_slots(days_ahead=14)
            slot_options = "\n".join(f"- {slot['display']}" for slot in slots[1:4])
            await self.send_scheduling_sms(
                to_number=contact.get("phone", ""),
                message=(
                    "No problem. Here are a few more options:\n"
                    f"{slot_options}\nWhich works? Or use {calendar.generate_booking_link()}"
                ),
            )
            return {"booked": False, "next_action": "waiting_for_slot_selection"}

        if "link" in msg_lower or "calendar" in msg_lower:
            await self.send_scheduling_sms(
                to_number=contact.get("phone", ""),
                message=f"You can book directly here: {calendar.generate_booking_link()}",
            )
            return {"booked": False, "next_action": "booking_link_sent"}

        return {"booked": False, "next_action": "unrecognized_intent"}


def _infer_timezone_label(contact: dict) -> str:
    location = f"{contact.get('city', '')} {contact.get('country', '')}".lower()
    if any(token in location for token in ["nairobi", "addis", "ethiopia", "kenya", "east africa"]):
        return "EAT"
    if any(token in location for token in ["london", "berlin", "paris", "amsterdam", "europe"]):
        return "CET/BST"
    return "ET"
