"""
Tenacious Conversion Engine - HubSpot CRM Integration
Normalizes contact objects and records downstream events for auditability.
"""

import os
from datetime import datetime, timezone
from typing import Optional

import httpx
import structlog

log = structlog.get_logger()


class HubSpotCRM:
    """HubSpot client with MCP primary transport and REST fallback."""

    BASE_URL = "https://api.hubapi.com"

    def __init__(self):
        self.access_token = os.getenv("HUBSPOT_ACCESS_TOKEN")
        self.transport = os.getenv("HUBSPOT_TRANSPORT", "rest").lower()
        self.mcp_url = os.getenv("HUBSPOT_MCP_URL", "http://localhost:8080/mcp")
        if not self.access_token:
            log.warning("hubspot_token_missing", msg="Set HUBSPOT_ACCESS_TOKEN in .env")

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    def _normalize_contact(self, contact: Optional[dict]) -> Optional[dict]:
        if not contact:
            return None
        properties = contact.get("properties", {})
        return {"id": contact.get("id"), **properties}

    async def _request(self, method: str, path: str, *, json: Optional[dict] = None) -> dict:
        if self.transport == "mcp":
            return await self._request_via_mcp(method, path, json=json)
        return await self._request_via_rest(method, path, json=json)

    async def _request_via_rest(self, method: str, path: str, *, json: Optional[dict] = None) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.request(
                method,
                f"{self.BASE_URL}{path}",
                headers=self._headers(),
                json=json,
            )
            if not resp.is_success:
                log.error("hubspot_api_error", method=method, path=path,
                          status=resp.status_code, body=resp.text[:500])
            resp.raise_for_status()
            return resp.json() if resp.content else {}

    async def _request_via_mcp(self, method: str, path: str, *, json: Optional[dict] = None) -> dict:
        payload = {
            "tool": "hubspot.http_request",
            "arguments": {
                "method": method,
                "path": path,
                "headers": self._headers(),
                "json": json or {},
            },
        }
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(self.mcp_url, json=payload)
                resp.raise_for_status()
                body = resp.json() if resp.content else {}
                if isinstance(body, dict) and "result" in body:
                    return body["result"] or {}
                return body
            except Exception as exc:
                log.warning("hubspot_mcp_request_failed_falling_back_to_rest", error=str(exc), path=path)
                return await self._request_via_rest(method, path, json=json)

    # Standard HubSpot contact properties — no schema scope needed.
    # Note: 'description' is a company property, NOT a valid contact property.
    _STANDARD_PROPS = {
        "firstname", "lastname", "email", "phone", "jobtitle", "company",
        "website", "city", "state", "country", "industry", "annualrevenue",
        "numberofemployees", "hs_lead_status", "lifecyclestage",
    }

    def _split_props(self, properties: dict) -> tuple[dict, dict]:
        """Split into standard props (safe) and custom props (need schema scope)."""
        standard = {k: v for k, v in properties.items() if k in self._STANDARD_PROPS}
        custom = {k: v for k, v in properties.items() if k not in self._STANDARD_PROPS}
        return standard, custom

    def _enrichment_note(self, properties: dict, extra_timestamp: str) -> str:
        """Format all enrichment fields as a readable note body."""
        lines = ["[TENACIOUS ENGINE] enrichment_snapshot"]
        for k, v in properties.items():
            if v:
                lines.append(f"{k}: {v}")
        lines.append(f"last_enriched_at: {extra_timestamp}")
        lines.append(f"data_source: tenacious_conversion_engine")
        return "\n".join(lines)

    async def upsert_contact(self, email: str, properties: dict) -> dict:
        search_resp = await self._request(
            "POST",
            "/crm/v3/objects/contacts/search",
            json={
                "filterGroups": [{
                    "filters": [{"propertyName": "email", "operator": "EQ", "value": email}]
                }]
            },
        )
        existing = search_resp.get("results", [])
        now_ts = datetime.now(timezone.utc).isoformat()

        standard_props, custom_props = self._split_props(properties)

        if existing:
            contact_id = existing[0]["id"]
            resp = await self._request(
                "PATCH",
                f"/crm/v3/objects/contacts/{contact_id}",
                json={"properties": standard_props},
            )
            log.info("hubspot_contact_updated", contact_id=contact_id, email=email)
            contact = self._normalize_contact(resp)
        else:
            resp = await self._request(
                "POST",
                "/crm/v3/objects/contacts",
                json={"properties": {"email": email, **standard_props}},
            )
            log.info("hubspot_contact_created", email=email)
            contact = self._normalize_contact(resp)

        # Try custom props separately — works if schema scope is granted later.
        if contact and contact.get("id") and custom_props:
            try:
                await self._request(
                    "PATCH",
                    f"/crm/v3/objects/contacts/{contact['id']}",
                    json={"properties": {
                        **custom_props,
                        "last_enriched_at": now_ts,
                        "data_source": "tenacious_conversion_engine",
                    }},
                )
                log.info("hubspot_custom_props_written", contact_id=contact["id"])
            except Exception as exc:
                log.warning("hubspot_custom_props_skipped", reason=str(exc),
                            note="Grant CRM schema write scope to the private app")
        return contact

    async def find_contact_by_email(self, email: str) -> Optional[dict]:
        resp = await self._request(
            "POST",
            "/crm/v3/objects/contacts/search",
            json={
                "filterGroups": [{
                    "filters": [{"propertyName": "email", "operator": "EQ", "value": email}]
                }],
                "properties": [
                    "email",
                    "firstname",
                    "lastname",
                    "company",
                    "phone",
                    "icp_segment",
                    "warm_lead",
                    "sms_consent",
                    "crunchbase_id",
                    "booking_id",
                    "booking_status",
                    "booking_start_time",
                ],
            },
        )
        results = resp.get("results", [])
        return self._normalize_contact(results[0]) if results else None

    async def find_contact_by_phone(self, phone: str) -> Optional[dict]:
        resp = await self._request(
            "POST",
            "/crm/v3/objects/contacts/search",
            json={
                "filterGroups": [{
                    "filters": [{"propertyName": "phone", "operator": "EQ", "value": phone}]
                }],
                "properties": [
                    "email",
                    "firstname",
                    "lastname",
                    "company",
                    "phone",
                    "warm_lead",
                    "sms_consent",
                    "crunchbase_id",
                    "booking_id",
                    "booking_status",
                ],
            },
        )
        results = resp.get("results", [])
        return self._normalize_contact(results[0]) if results else None

    async def update_contact(self, contact_id: str, properties: dict) -> dict:
        try:
            resp = await self._request(
                "PATCH",
                f"/crm/v3/objects/contacts/{contact_id}",
                json={"properties": properties},
            )
            return self._normalize_contact(resp)
        except Exception as exc:
            log.warning("hubspot_update_contact_failed", contact_id=contact_id,
                        error=str(exc), note="Custom props likely need schema scope")
            return {"id": contact_id}

    async def update_contact_by_phone(self, phone: str, properties: dict) -> Optional[dict]:
        contact = await self.find_contact_by_phone(phone)
        if contact:
            return await self.update_contact(contact["id"], properties)
        return None

    async def log_activity(self, contact_id: str, activity_type: str, details: dict) -> dict:
        note_body = f"[TENACIOUS ENGINE] {activity_type}\n" + "\n".join(
            f"{key}: {value}" for key, value in details.items()
        )
        resp = await self._request(
            "POST",
            "/crm/v3/objects/notes",
            json={
                "properties": {
                    "hs_note_body": note_body,
                    "hs_timestamp": datetime.now(timezone.utc).isoformat(),
                },
                "associations": [{
                    "to": {"id": contact_id},
                    "types": [{
                        "associationCategory": "HUBSPOT_DEFINED",
                        "associationTypeId": 202,
                    }],
                }],
            },
        )
        log.info("hubspot_activity_logged", contact_id=contact_id, activity_type=activity_type)
        return resp

    async def mark_warm_lead(self, contact_id: str, *, sms_consent: bool, source: str) -> dict:
        return await self.update_contact(contact_id, {
            "warm_lead": "true",
            "sms_consent": "true" if sms_consent else "false",
            "warm_lead_source": source,
            "warm_lead_at": datetime.now(timezone.utc).isoformat(),
        })

    async def record_booking_completion(self, contact_id: str, booking: dict) -> dict:
        booking_id = booking.get("booking_id") or booking.get("id")
        update = await self.update_contact(contact_id, {
            "booking_id": booking_id,
            "booking_status": booking.get("status", "confirmed"),
            "booking_start_time": booking.get("start_time") or booking.get("call_time", ""),
            "warm_lead": "true",
        })
        try:
            await self.log_activity(contact_id, "booking_completed", {
                "booking_id": booking_id,
                "status": booking.get("status", "confirmed"),
                "start_time": booking.get("start_time") or booking.get("call_time", ""),
                "channel": booking.get("channel", "unknown"),
            })
        except Exception as exc:
            log.warning("hubspot_log_booking_activity_failed", error=str(exc))
        return update

    async def record_email_bounce(self, recipient: str, bounce: dict) -> Optional[dict]:
        contact = await self.find_contact_by_email(recipient)
        if not contact:
            return None
        await self.update_contact(contact["id"], {
            "email_bounced": "true",
            "email_bounce_reason": bounce.get("reason", "unknown"),
            "email_bounced_at": datetime.now(timezone.utc).isoformat(),
        })
        try:
            await self.log_activity(contact["id"], "email_bounce", bounce)
        except Exception as exc:
            log.warning("hubspot_log_bounce_activity_failed", error=str(exc))
        return contact
