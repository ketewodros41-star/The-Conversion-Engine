"""
Tenacious Conversion Engine - Main Orchestrator
Multi-agent autonomous lead generation and conversion system.
"""

import os
from datetime import datetime, timezone
from typing import Optional

import structlog
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from calcom_booking import CalComBooking
from channel_policy import ChannelPolicy
from email_handler import EmailHandler
from enrichment import EnrichmentPipeline
from event_bus import EventBus
from hubspot_crm import HubSpotCRM
from icp_classifier import ICPClassifier
from outreach_generator import OutreachGenerator
from sms_handler import SMSHandler

load_dotenv()
log = structlog.get_logger()

LIVE_MODE = os.getenv("LIVE_MODE", "false").lower() == "true"

app = FastAPI(title="Tenacious Conversion Engine", version="1.0.0")
event_bus = EventBus()

enrichment = EnrichmentPipeline()
email_handler = EmailHandler(live_mode=LIVE_MODE, event_bus=event_bus)
sms_handler = SMSHandler(live_mode=LIVE_MODE, event_bus=event_bus)
crm = HubSpotCRM()
calendar = CalComBooking(event_bus=event_bus)
outreach_gen = OutreachGenerator()
icp_classifier = ICPClassifier()
channel_policy = ChannelPolicy()


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


class EmailBounceWebhook(BaseModel):
    recipient: str
    event_type: str = "bounce"
    message_id: Optional[str] = None
    reason: Optional[str] = None


class CalComBookingWebhook(BaseModel):
    event: Optional[str] = None
    trigger_event: Optional[str] = None
    status: Optional[str] = None
    booking: dict


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    log.warning("malformed_webhook_payload", path=str(request.url.path), errors=exc.errors())
    return JSONResponse(status_code=400, content={"status": "invalid_payload", "errors": exc.errors()})


async def _handle_email_bounce_event(event: dict) -> None:
    await crm.record_email_bounce(event["recipient"], event)


async def _handle_calcom_booking_completed(event: dict) -> None:
    contact = None
    if event.get("attendee_email"):
        contact = await crm.find_contact_by_email(event["attendee_email"])
    if not contact and event.get("attendee_phone"):
        contact = await crm.find_contact_by_phone(event["attendee_phone"])
    if not contact:
        log.warning("calcom_booking_contact_not_found", booking_id=event.get("booking_id"))
        return
    await crm.record_booking_completion(contact["id"], {
        **event,
        "channel": "calcom",
        "status": event.get("status", "confirmed"),
    })


email_handler.on_bounce(_handle_email_bounce_event)
calendar.on_booking_completed(_handle_calcom_booking_completed)


async def process_prospect(prospect: ProspectRequest) -> dict:
    start_time = datetime.now(timezone.utc)
    log.info(
        "prospect_processing_started",
        company=prospect.company_name,
        crunchbase_id=prospect.crunchbase_id,
        live_mode=LIVE_MODE,
    )

    hiring_brief = await enrichment.build_hiring_signal_brief(
        crunchbase_id=prospect.crunchbase_id,
        company_name=prospect.company_name,
    )
    competitor_brief = await enrichment.build_competitor_gap_brief(
        crunchbase_id=prospect.crunchbase_id,
        sector=hiring_brief["prospect"]["industry"],
        prospect_ai_score=hiring_brief["signals"]["ai_maturity"]["score"],
    )

    classification = icp_classifier.classify(hiring_brief)
    email_variant = (
        classification["primary_segment"]
        if classification["confidence"] >= 0.65 else
        "exploratory"
    )

    bench_check = await enrichment.check_bench_availability(
        required_skills=hiring_brief["signals"]["tech_stack"]["details"]["bench_match"]
        if hiring_brief["signals"]["tech_stack"]["present"] else []
    )

    outreach_email = outreach_gen.generate_outbound_email(
        prospect=prospect.model_dump(),
        hiring_brief=hiring_brief,
        competitor_brief=competitor_brief,
        segment=email_variant,
        bench_available=bench_check["available"],
        live_mode=LIVE_MODE,
    )

    email_result = await email_handler.send_outbound(
        to_email=prospect.contact_email,
        subject=outreach_email["subject"],
        body=outreach_email["body"],
        metadata={
            "is_draft": True,
            "variant": email_variant,
            "crunchbase_id": prospect.crunchbase_id,
            "is_synthetic": prospect.is_synthetic,
        },
    )

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
            "funding_event": hiring_brief["signals"]["funding_event"].get("brief_language", ""),
            "job_post_velocity": hiring_brief["signals"]["job_post_velocity"].get("brief_language", ""),
            "leadership_change": hiring_brief["signals"]["leadership_change"].get("brief_language", ""),
            "last_enriched_at": start_time.isoformat(),
            "outreach_variant": email_variant,
            "is_synthetic": str(prospect.is_synthetic).lower(),
        },
    )
    await crm.log_activity(
        contact_id=hubspot_contact["id"],
        activity_type="outbound_email_sent",
        details={
            "message_id": email_result.get("message_id", ""),
            "variant": email_variant,
            "ai_maturity_score": hiring_brief["signals"]["ai_maturity"]["score"],
            "sent_at": start_time.isoformat(),
        },
    )

    elapsed_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
    log.info(
        "prospect_processing_complete",
        company=prospect.company_name,
        elapsed_ms=elapsed_ms,
        email_sent=email_result["sent"],
        hubspot_id=hubspot_contact.get("id"),
    )
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
    log.info("inbound_email_received", from_email=webhook.from_email, subject=webhook.subject)
    await email_handler.process_inbound_reply(webhook.model_dump())

    contact = await crm.find_contact_by_email(webhook.from_email)
    if not contact:
        log.warning("inbound_email_unknown_sender", email=webhook.from_email)
        raise HTTPException(status_code=404, detail="Prospect not found in CRM")

    reply_intent = outreach_gen.classify_reply_intent(webhook.body)

    if reply_intent == "schedule":
        await crm.mark_warm_lead(
            contact["id"],
            sms_consent=str(contact.get("sms_consent", "")).lower() == "true",
            source="email_reply_schedule_intent",
        )
        contact["warm_lead"] = "true"
        slots = await calendar.get_available_slots(days_ahead=7)
        response = outreach_gen.generate_scheduling_reply(
            contact=contact,
            slots=slots,
            channel="email",
            booking_link=calendar.generate_booking_link(),
        )
        await email_handler.send_reply(
            to_email=webhook.from_email,
            subject=f"Re: {webhook.subject}",
            body=response["body"],
            in_reply_to=webhook.message_id,
            metadata={"is_draft": True, "intent": "scheduling"},
        )
        sms_decision = channel_policy.can_offer_sms_follow_up(contact, reply_intent)
        if sms_decision.allowed:
            await sms_handler.send_scheduling_sms(
                to_number=contact["phone"],
                message=response["sms_follow_up"],
            )
            await crm.log_activity(
                contact_id=contact["id"],
                activity_type="sms_follow_up_sent",
                details={
                    "reason": sms_decision.reason,
                    "booking_link": calendar.generate_booking_link(),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )
        else:
            log.info("sms_follow_up_skipped", reason=sms_decision.reason, email=webhook.from_email)
    elif reply_intent == "qualify":
        response = outreach_gen.generate_qualification_reply(contact=contact, email_body=webhook.body)
        await email_handler.send_reply(
            to_email=webhook.from_email,
            subject=f"Re: {webhook.subject}",
            body=response["body"],
            in_reply_to=webhook.message_id,
            metadata={"is_draft": True, "intent": "qualification"},
        )
    elif reply_intent == "unsubscribe":
        await crm.update_contact(contact["id"], {"email_opt_out": "true"})
        log.info("prospect_unsubscribed", email=webhook.from_email)
        return {"status": "unsubscribed"}

    await crm.log_activity(
        contact_id=contact["id"],
        activity_type="email_reply",
        details={
            "intent": reply_intent,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message_id": webhook.message_id,
        },
    )
    return {"status": "handled", "intent": reply_intent}


@app.post("/webhook/email/bounce")
async def handle_email_bounce(webhook: EmailBounceWebhook):
    event = await email_handler.process_bounce_event(webhook.model_dump())
    return {"status": "handled", "event": event["event_type"]}


@app.post("/webhook/sms/inbound")
async def handle_inbound_sms(webhook: InboundSMSWebhook):
    log.info("inbound_sms_received", from_number=webhook.from_number)

    if webhook.message.strip().upper() in {"STOP", "UNSUBSCRIBE", "QUIT", "CANCEL"}:
        await sms_handler.handle_stop(webhook.from_number)
        await crm.update_contact_by_phone(
            webhook.from_number,
            {"sms_opt_out": "true", "sms_opt_out_at": webhook.timestamp},
        )
        return {"status": "stopped"}

    contact = await crm.find_contact_by_phone(webhook.from_number)
    sms_decision = channel_policy.can_accept_inbound_sms(contact)
    if not sms_decision.allowed:
        log.warning("unexpected_cold_sms", number=webhook.from_number, reason=sms_decision.reason)
        return {"status": "ignored_cold_contact"}

    booking_result = await sms_handler.handle_scheduling_message(
        contact=contact,
        message=webhook.message,
        calendar=calendar,
    )

    if booking_result["booked"]:
        await crm.record_booking_completion(contact["id"], {
            "id": booking_result["event_id"],
            "booking_id": booking_result["event_id"],
            "status": "confirmed",
            "call_time": booking_result["call_time"],
            "channel": "sms",
        })
        await crm.log_activity(
            contact_id=contact["id"],
            activity_type="discovery_call_booked",
            details={
                "channel": "sms",
                "call_time": booking_result["call_time"],
                "cal_event_id": booking_result["event_id"],
                "timestamp": webhook.timestamp,
            },
        )
    return {"status": "handled", "booked": booking_result["booked"]}


@app.post("/webhook/calcom/booking")
async def handle_calcom_booking(webhook: CalComBookingWebhook):
    event = await calendar.process_booking_webhook(webhook.model_dump())
    return {"status": "handled", "booking_id": event.get("booking_id")}


@app.post("/api/process-prospect")
async def api_process_prospect(prospect: ProspectRequest):
    try:
        return await process_prospect(prospect)
    except Exception as exc:
        import traceback
        log.error("process_prospect_unhandled", error=str(exc), tb=traceback.format_exc())
        raise HTTPException(status_code=500, detail={"error": str(exc), "type": type(exc).__name__})


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "live_mode": LIVE_MODE,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
