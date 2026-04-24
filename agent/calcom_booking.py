"""
Tenacious Conversion Engine - Cal.com Booking Flow
Self-hosted Cal.com (Docker Compose). Books discovery calls with Tenacious delivery leads.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx
import structlog

from event_bus import EventBus

log = structlog.get_logger()

CALCOM_BASE_URL = os.getenv("CALCOM_URL", "http://localhost:3000")
CALCOM_API_KEY = os.getenv("CALCOM_API_KEY", "")
DISCOVERY_CALL_EVENT_TYPE_ID = int(os.getenv("CALCOM_EVENT_TYPE_ID", "1"))


class CalComBooking:
    """Cal.com REST integration with downstream booking-completion hooks."""

    def __init__(self, event_bus: Optional[EventBus] = None):
        self.event_bus = event_bus or EventBus()

    def on_booking_completed(self, handler) -> None:
        self.event_bus.subscribe("calcom.booking.completed", handler)

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {CALCOM_API_KEY}",
            "Content-Type": "application/json",
        }

    def generate_booking_link(self) -> str:
        return f"{CALCOM_BASE_URL.rstrip('/')}/bookings/{DISCOVERY_CALL_EVENT_TYPE_ID}"

    async def get_available_slots(self, days_ahead: int = 7) -> list:
        start = datetime.now(timezone.utc)
        end = start + timedelta(days=days_ahead)

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(
                    f"{CALCOM_BASE_URL}/api/v1/slots",
                    headers=self._headers(),
                    params={
                        "eventTypeId": DISCOVERY_CALL_EVENT_TYPE_ID,
                        "startTime": start.isoformat(),
                        "endTime": end.isoformat(),
                        "timeZone": "America/New_York",
                    },
                )
                resp.raise_for_status()
                slots_data = resp.json().get("slots", {})
                formatted = []
                for _, day_slots in slots_data.items():
                    for slot in day_slots[:2]:
                        dt = datetime.fromisoformat(slot["time"].replace("Z", "+00:00"))
                        formatted.append({
                            "id": slot["time"],
                            "datetime": slot["time"],
                            "display": dt.strftime("%A, %B %d at %I:%M %p ET").lstrip("0"),
                        })
                return formatted[:6]
            except Exception as exc:
                log.error("calcom_slots_fetch_failed", error=str(exc))
                return [
                    {
                        "id": "slot_1",
                        "datetime": "2026-04-28T19:00:00Z",
                        "display": "Monday, April 28 at 3:00 PM ET",
                    },
                    {
                        "id": "slot_2",
                        "datetime": "2026-04-29T15:00:00Z",
                        "display": "Tuesday, April 29 at 11:00 AM ET",
                    },
                    {
                        "id": "slot_3",
                        "datetime": "2026-04-30T18:00:00Z",
                        "display": "Wednesday, April 30 at 2:00 PM ET",
                    },
                ]

    async def book_slot(
        self,
        slot_id: str,
        attendee_email: str,
        attendee_name: str,
        attendee_phone: Optional[str] = None,
        context_brief: Optional[str] = None,
    ) -> dict:
        async with httpx.AsyncClient() as client:
            try:
                payload = {
                    "eventTypeId": DISCOVERY_CALL_EVENT_TYPE_ID,
                    "start": slot_id,
                    "responses": {
                        "name": attendee_name,
                        "email": attendee_email,
                        "phone": attendee_phone or "",
                        "notes": context_brief or "Discovery call booked by Tenacious Conversion Engine [DRAFT]",
                    },
                    "timeZone": "America/New_York",
                    "language": "en",
                    "metadata": {
                        "source": "tenacious_conversion_engine",
                        "is_draft": "true",
                    },
                }
                resp = await client.post(
                    f"{CALCOM_BASE_URL}/api/v1/bookings",
                    headers=self._headers(),
                    json=payload,
                )
                resp.raise_for_status()
                booking = resp.json()
                booking["attendee_email"] = attendee_email
                booking["attendee_phone"] = attendee_phone or ""
                log.info(
                    "discovery_call_booked",
                    attendee=attendee_email,
                    slot=slot_id,
                    booking_id=booking.get("id"),
                )
                return booking
            except Exception as exc:
                log.error("calcom_booking_failed", error=str(exc))
                return {
                    "id": f"synthetic_booking_{slot_id}",
                    "attendee_email": attendee_email,
                    "attendee_phone": attendee_phone or "",
                    "error": str(exc),
                }

    async def get_booking_status(self, booking_id: str) -> dict:
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(
                    f"{CALCOM_BASE_URL}/api/v1/bookings/{booking_id}",
                    headers=self._headers(),
                )
                resp.raise_for_status()
                return resp.json()
            except Exception as exc:
                log.error("calcom_status_fetch_failed", error=str(exc))
                return {"status": "unknown", "error": str(exc)}

    async def process_booking_webhook(self, payload: dict) -> dict:
        booking = payload.get("booking", payload)
        event = {
            "booking_id": booking.get("id"),
            "status": str(payload.get("status", booking.get("status", ""))).lower(),
            "event_type": str(payload.get("event", payload.get("trigger_event", ""))).lower(),
            "attendee_email": booking.get("attendee_email") or booking.get("email"),
            "attendee_phone": booking.get("attendee_phone") or booking.get("phone"),
            "start_time": booking.get("startTime") or booking.get("start"),
            "raw": payload,
        }
        if event["status"] in {"confirmed", "accepted", "completed"} or event["event_type"] in {
            "booking.completed",
            "booking_confirmed",
        }:
            await self.event_bus.emit("calcom.booking.completed", event)
        return event
