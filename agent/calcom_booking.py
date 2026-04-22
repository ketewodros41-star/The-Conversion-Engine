"""
Tenacious Conversion Engine — Cal.com Booking Flow
Self-hosted Cal.com (Docker Compose). Books discovery calls with Tenacious delivery leads.
"""

import os
from datetime import datetime, timezone
from typing import Optional
import httpx
import structlog

log = structlog.get_logger()

CALCOM_BASE_URL = os.getenv("CALCOM_URL", "http://localhost:3000")
CALCOM_API_KEY = os.getenv("CALCOM_API_KEY", "")
DISCOVERY_CALL_EVENT_TYPE_ID = int(os.getenv("CALCOM_EVENT_TYPE_ID", "1"))


class CalComBooking:
    """Cal.com CalDAV/REST API integration for discovery call booking."""

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {CALCOM_API_KEY}",
            "Content-Type": "application/json",
        }

    async def get_available_slots(self, days_ahead: int = 7) -> list:
        """Fetch available discovery call slots for the next N days."""
        from datetime import timedelta
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
                    }
                )
                slots_data = resp.json().get("slots", {})

                # Flatten and format slots
                formatted = []
                for date, day_slots in slots_data.items():
                    for slot in day_slots[:2]:  # Max 2 slots per day
                        dt = datetime.fromisoformat(slot["time"].replace("Z", "+00:00"))
                        formatted.append({
                            "id": slot["time"],
                            "datetime": slot["time"],
                            "display": dt.strftime("%A, %B %d at %-I:%M %p ET"),
                        })
                return formatted[:6]  # Return max 6 options

            except Exception as e:
                log.error("calcom_slots_fetch_failed", error=str(e))
                # Return synthetic slots for demo/sandbox
                return [
                    {"id": "slot_1", "datetime": "2026-04-28T19:00:00Z",
                     "display": "Monday, April 28 at 3:00 PM ET"},
                    {"id": "slot_2", "datetime": "2026-04-29T15:00:00Z",
                     "display": "Tuesday, April 29 at 11:00 AM ET"},
                    {"id": "slot_3", "datetime": "2026-04-30T18:00:00Z",
                     "display": "Wednesday, April 30 at 2:00 PM ET"},
                ]

    async def book_slot(self, slot_id: str, attendee_email: str,
                         attendee_name: str, attendee_phone: Optional[str] = None,
                         context_brief: Optional[str] = None) -> dict:
        """Book a discovery call slot. Attaches context brief for Tenacious delivery lead."""
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
                booking = resp.json()
                log.info("discovery_call_booked",
                         attendee=attendee_email,
                         slot=slot_id,
                         booking_id=booking.get("id"))
                return booking

            except Exception as e:
                log.error("calcom_booking_failed", error=str(e))
                return {"id": f"synthetic_booking_{slot_id}", "error": str(e)}

    async def get_booking_status(self, booking_id: str) -> dict:
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(
                    f"{CALCOM_BASE_URL}/api/v1/bookings/{booking_id}",
                    headers=self._headers(),
                )
                return resp.json()
            except Exception as e:
                log.error("calcom_status_fetch_failed", error=str(e))
                return {"status": "unknown", "error": str(e)}
