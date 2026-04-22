"""
Tenacious Conversion Engine — Main Orchestrator
Multi-agent autonomous lead generation and conversion system.

IMPORTANT: LIVE_MODE defaults to False. Set LIVE_MODE=true only after
Tenacious executive team review and approval. All outbound routes to
staff sink when LIVE_MODE=false.
"""

import asyncio
import os
import json
import logging
from datetime import datetime, timezone
from typing import Optional

import structlog
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel

from enrichment import EnrichmentPipeline
from email_handler import EmailHandler
from sms_handler import SMSHandler
from hubspot_crm import HubSpotCRM
from calcom_booking import CalComBooking
from outreach_generator import OutreachGenerator
from icp_classifier import ICPClassifier

load_dotenv()
log = structlog.get_logger()

# === KILL SWITCH ===
# Default: False. All outbound routes to staff sink.
# Set to true only after Tenacious approval.
LIVE_MODE = os.getenv("LIVE_MODE", "false").lower() == "true"

app = FastAPI(title="Tenacious Conversion Engine", version="1.0.0")

# Initialize components
enrichment = EnrichmentPipeline()
email_handler = EmailHandler(live_mode=LIVE_MODE)
sms_handler = SMSHandler(live_mode=LIVE_MODE)
crm = HubSpotCRM()
calendar = CalComBooking()
outreach_gen = OutreachGenerator()
icp_classifier = ICPClassifier()


class ProspectRequest(BaseModel):
    crunchbase_id: str
    company_name: str
    contact_email: str
    contact_name: str
    contact_title: str
    is_synthetic: bool = True


class InboundEmailWebhook(BaseModel):
    from_email: str
    subject: str
    body: str
    in_reply_to: Optional[str] = None
    message_id: str


class InboundSMSWebhook(BaseModel):
    from_number: str
    to_number: str
    message: str
    timestamp: str


async def process_prospect(prospect: ProspectRequest) -> dict:
    """Full prospect processing pipeline: enrich → classify → outreach → CRM."""

    start_time = datetime.now(timezone.utc)
    log.info("prospect_processing_started", company=prospect.company_name,
             crunchbase_id=prospect.crunchbase_id, live_mode=LIVE_MODE)

    # Phase 1: Signal enrichment
    hiring_brief = await enrichment.build_hiring_signal_brief(
        crunchbase_id=prospect.crunchbase_id,
        company_name=prospect.company_name,
    )
    competitor_brief = await enrichment.build_competitor_gap_brief(
        crunchbase_id=prospect.crunchbase_id,
        sector=hiring_brief["prospect"]["industry"],
    )

    # Phase 2: ICP classification (with abstention if confidence < threshold)
    classification = icp_classifier.classify(hiring_brief)
    if classification["confidence"] < 0.65:
        log.warning("icp_classification_low_confidence",
                    company=prospect.company_name,
                    confidence=classification["confidence"])
        # Abstain: send exploratory email rather than segment-specific pitch
        email_variant = "exploratory"
    else:
        email_variant = classification["primary_segment"]

    # Phase 3: Bench-to-brief check (HARD CONSTRAINT: never over-commit)
    bench_check = await enrichment.check_bench_availability(
        required_skills=hiring_brief["signals"]["tech_stack"]["details"]["bench_match"]
        if hiring_brief["signals"]["tech_stack"]["present"] else []
    )

    # Phase 4: Generate outreach email
    outreach_email = outreach_gen.generate_outbound_email(
        prospect=prospect.dict(),
        hiring_brief=hiring_brief,
        competitor_brief=competitor_brief,
        segment=email_variant,
        bench_available=bench_check["available"],
        live_mode=LIVE_MODE,
    )

    # Phase 5: Send email (routes to staff sink if LIVE_MODE=false)
    email_result = await email_handler.send_outbound(
        to_email=prospect.contact_email,
        subject=outreach_email["subject"],
        body=outreach_email["body"],
        metadata={
            "is_draft": True,  # REQUIRED: all branded content marked 'draft'
            "variant": email_variant,
            "crunchbase_id": prospect.crunchbase_id,
            "is_synthetic": prospect.is_synthetic,
        }
    )

    # Phase 6: Log to HubSpot CRM
    hubspot_contact = await crm.upsert_contact(
        email=prospect.contact_email,
        properties={
            "firstname": prospect.contact_name.split()[0],
            "lastname": " ".join(prospect.contact_name.split()[1:]),
            "jobtitle": prospect.contact_title,
            "company": prospect.company_name,
            "crunchbase_id": prospect.crunchbase_id,
            "icp_segment": email_variant,
            "icp_confidence": str(classification["confidence"]),
            "ai_maturity_score": str(hiring_brief["signals"]["ai_maturity"]["score"]),
            "funding_event": hiring_brief["signals"]["funding_event"]["brief_language"],
            "job_post_velocity": hiring_brief["signals"]["job_post_velocity"]["brief_language"],
            "last_enriched_at": start_time.isoformat(),
            "outreach_variant": email_variant,
            "is_synthetic": str(prospect.is_synthetic),
        }
    )

    elapsed_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
    log.info("prospect_processing_complete",
             company=prospect.company_name,
             elapsed_ms=elapsed_ms,
             email_sent=email_result["sent"],
             hubspot_id=hubspot_contact.get("id"))

    return {
        "status": "processed",
        "prospect": prospect.company_name,
        "crunchbase_id": prospect.crunchbase_id,
        "icp_segment": email_variant,
        "icp_confidence": classification["confidence"],
        "email_sent": email_result["sent"],
        "hubspot_id": hubspot_contact.get("id"),
        "elapsed_ms": elapsed_ms,
        "live_mode": LIVE_MODE,
    }


@app.post("/webhook/email/inbound")
async def handle_inbound_email(webhook: InboundEmailWebhook):
    """Handle inbound email replies from prospects."""
    log.info("inbound_email_received", from_email=webhook.from_email,
             subject=webhook.subject)

    # Look up prospect in CRM
    contact = await crm.find_contact_by_email(webhook.from_email)
    if not contact:
        log.warning("inbound_email_unknown_sender", email=webhook.from_email)
        raise HTTPException(status_code=404, detail="Prospect not found in CRM")

    # Determine reply intent (qualify, object, schedule, unsubscribe)
    reply_intent = outreach_gen.classify_reply_intent(webhook.body)

    if reply_intent == "schedule":
        # Warm lead — offer calendar slots and optionally escalate to SMS
        slots = await calendar.get_available_slots(days_ahead=7)
        response = outreach_gen.generate_scheduling_reply(
            contact=contact,
            slots=slots,
            channel="email"
        )
        await email_handler.send_reply(
            to_email=webhook.from_email,
            subject=f"Re: {webhook.subject}",
            body=response["body"],
            in_reply_to=webhook.message_id,
            metadata={"is_draft": True, "intent": "scheduling"}
        )
        # If prospect consented to SMS, offer faster coordination
        if contact.get("sms_consent") and reply_intent == "schedule":
            await sms_handler.send_scheduling_sms(
                to_number=contact.get("phone"),
                message=response["sms_follow_up"],
            )

    elif reply_intent == "qualify":
        # Continue qualification conversation
        response = outreach_gen.generate_qualification_reply(
            contact=contact,
            email_body=webhook.body,
        )
        await email_handler.send_reply(
            to_email=webhook.from_email,
            subject=f"Re: {webhook.subject}",
            body=response["body"],
            in_reply_to=webhook.message_id,
            metadata={"is_draft": True, "intent": "qualification"}
        )

    elif reply_intent == "unsubscribe":
        await crm.update_contact(contact["id"], {"email_opt_out": True})
        log.info("prospect_unsubscribed", email=webhook.from_email)
        return {"status": "unsubscribed"}

    # Update CRM with reply event
    await crm.log_activity(
        contact_id=contact["id"],
        activity_type="email_reply",
        details={
            "intent": reply_intent,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message_id": webhook.message_id,
        }
    )

    return {"status": "handled", "intent": reply_intent}


@app.post("/webhook/sms/inbound")
async def handle_inbound_sms(webhook: InboundSMSWebhook):
    """Handle inbound SMS from warm leads (email-to-SMS channel handoff only)."""
    log.info("inbound_sms_received", from_number=webhook.from_number)

    # STOP command — mandatory handling
    if webhook.message.strip().upper() in ["STOP", "UNSUBSCRIBE", "QUIT", "CANCEL"]:
        await sms_handler.handle_stop(webhook.from_number)
        await crm.update_contact_by_phone(
            webhook.from_number,
            {"sms_opt_out": True, "sms_opt_out_at": webhook.timestamp}
        )
        log.info("sms_stop_command_processed", number=webhook.from_number)
        return {"status": "stopped"}

    # Scheduling SMS (secondary channel for warm leads only)
    contact = await crm.find_contact_by_phone(webhook.from_number)
    if not contact or not contact.get("warm_lead"):
        # Cold SMS — should not happen; log anomaly
        log.warning("unexpected_cold_sms", number=webhook.from_number)
        return {"status": "ignored_cold_contact"}

    # Parse scheduling intent from SMS
    booking_result = await sms_handler.handle_scheduling_message(
        contact=contact,
        message=webhook.message,
        calendar=calendar,
    )

    if booking_result["booked"]:
        await crm.log_activity(
            contact_id=contact["id"],
            activity_type="discovery_call_booked",
            details={
                "channel": "sms",
                "call_time": booking_result["call_time"],
                "cal_event_id": booking_result["event_id"],
                "timestamp": webhook.timestamp,
            }
        )
        log.info("discovery_call_booked",
                 company=contact.get("company"),
                 call_time=booking_result["call_time"])

    return {"status": "handled", "booked": booking_result["booked"]}


@app.post("/api/process-prospect")
async def api_process_prospect(prospect: ProspectRequest):
    """API endpoint to trigger prospect processing pipeline."""
    result = await process_prospect(prospect)
    return result


@app.get("/health")
async def health():
    return {"status": "ok", "live_mode": LIVE_MODE,
            "timestamp": datetime.now(timezone.utc).isoformat()}


if __name__ == "__main__":
    import uvicorn
    if LIVE_MODE:
        log.warning("LIVE_MODE_ENABLED",
                    message="System is in live mode. All outbound will reach real prospects.")
    else:
        log.info("SANDBOX_MODE",
                 message="LIVE_MODE=false. All outbound routes to staff sink.")
    uvicorn.run(app, host="0.0.0.0", port=8000)
