"""
Tenacious Conversion Engine — HubSpot CRM Integration
Uses HubSpot MCP server. Every conversation event is written to HubSpot.
All records include crunchbase_id and last_enriched_at timestamp.
"""

import os
from datetime import datetime, timezone
from typing import Optional
import httpx
import structlog

log = structlog.get_logger()

HUBSPOT_BASE_URL = "https://api.hubapi.com"


class HubSpotCRM:
    """HubSpot Developer Sandbox integration for Tenacious lead management."""

    def __init__(self):
        self.access_token = os.getenv("HUBSPOT_ACCESS_TOKEN")
        if not self.access_token:
            log.warning("hubspot_token_missing", msg="Set HUBSPOT_ACCESS_TOKEN in .env")

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    async def upsert_contact(self, email: str, properties: dict) -> dict:
        """Create or update a contact. Returns the HubSpot contact object."""
        async with httpx.AsyncClient() as client:
            # Search for existing contact
            search_resp = await client.post(
                f"{HUBSPOT_BASE_URL}/crm/v3/objects/contacts/search",
                headers=self._headers(),
                json={
                    "filterGroups": [{
                        "filters": [{"propertyName": "email", "operator": "EQ", "value": email}]
                    }]
                }
            )
            existing = search_resp.json().get("results", [])

            # Required fields: all non-null, enrichment timestamp present
            enriched_props = {
                **properties,
                "last_enriched_at": datetime.now(timezone.utc).isoformat(),
                "data_source": "tenacious_conversion_engine",
                "is_draft": "true",  # Branded content marked draft
            }

            if existing:
                contact_id = existing[0]["id"]
                resp = await client.patch(
                    f"{HUBSPOT_BASE_URL}/crm/v3/objects/contacts/{contact_id}",
                    headers=self._headers(),
                    json={"properties": enriched_props}
                )
                log.info("hubspot_contact_updated", contact_id=contact_id, email=email)
                return resp.json()
            else:
                resp = await client.post(
                    f"{HUBSPOT_BASE_URL}/crm/v3/objects/contacts",
                    headers=self._headers(),
                    json={"properties": {"email": email, **enriched_props}}
                )
                log.info("hubspot_contact_created", email=email)
                return resp.json()

    async def find_contact_by_email(self, email: str) -> Optional[dict]:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{HUBSPOT_BASE_URL}/crm/v3/objects/contacts/search",
                headers=self._headers(),
                json={
                    "filterGroups": [{
                        "filters": [{"propertyName": "email", "operator": "EQ", "value": email}]
                    }],
                    "properties": ["email", "firstname", "lastname", "company",
                                   "phone", "icp_segment", "warm_lead", "sms_consent"]
                }
            )
            results = resp.json().get("results", [])
            return results[0] if results else None

    async def find_contact_by_phone(self, phone: str) -> Optional[dict]:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{HUBSPOT_BASE_URL}/crm/v3/objects/contacts/search",
                headers=self._headers(),
                json={
                    "filterGroups": [{
                        "filters": [{"propertyName": "phone", "operator": "EQ", "value": phone}]
                    }]
                }
            )
            results = resp.json().get("results", [])
            return results[0] if results else None

    async def update_contact(self, contact_id: str, properties: dict) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.patch(
                f"{HUBSPOT_BASE_URL}/crm/v3/objects/contacts/{contact_id}",
                headers=self._headers(),
                json={"properties": properties}
            )
            return resp.json()

    async def update_contact_by_phone(self, phone: str, properties: dict) -> Optional[dict]:
        contact = await self.find_contact_by_phone(phone)
        if contact:
            return await self.update_contact(contact["id"], properties)
        return None

    async def log_activity(self, contact_id: str, activity_type: str, details: dict) -> dict:
        """Log a conversation event against a contact (audit trail)."""
        async with httpx.AsyncClient() as client:
            note_body = f"[TENACIOUS ENGINE] {activity_type}\n" + \
                        "\n".join(f"{k}: {v}" for k, v in details.items())
            resp = await client.post(
                f"{HUBSPOT_BASE_URL}/crm/v3/objects/notes",
                headers=self._headers(),
                json={
                    "properties": {
                        "hs_note_body": note_body,
                        "hs_timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                    "associations": [{
                        "to": {"id": contact_id},
                        "types": [{"associationCategory": "HUBSPOT_DEFINED",
                                   "associationTypeId": 202}]
                    }]
                }
            )
            log.info("hubspot_activity_logged", contact_id=contact_id,
                     activity_type=activity_type)
            return resp.json()
