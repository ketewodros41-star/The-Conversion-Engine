"""
Centralized channel handoff policy.

This module keeps cross-channel transition rules in one place so email, SMS,
CRM, and scheduling flows do not drift independently.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ChannelDecision:
    allowed: bool
    reason: str


class ChannelPolicy:
    """Owns cold-to-warm channel transitions and SMS gating."""

    @staticmethod
    def can_offer_sms_follow_up(contact: dict, reply_intent: str) -> ChannelDecision:
        if reply_intent != "schedule":
            return ChannelDecision(False, "sms_follow_up_only_for_scheduling")
        if str(contact.get("warm_lead", "")).lower() != "true":
            return ChannelDecision(False, "contact_not_marked_warm")
        if str(contact.get("sms_consent", "")).lower() != "true":
            return ChannelDecision(False, "sms_consent_missing")
        if not contact.get("phone"):
            return ChannelDecision(False, "phone_missing")
        return ChannelDecision(True, "warm_lead_with_sms_consent")

    @staticmethod
    def can_accept_inbound_sms(contact: dict | None) -> ChannelDecision:
        if not contact:
            return ChannelDecision(False, "unknown_phone")
        if str(contact.get("warm_lead", "")).lower() != "true":
            return ChannelDecision(False, "warm_lead_required")
        if str(contact.get("sms_opt_out", "")).lower() == "true":
            return ChannelDecision(False, "sms_opted_out")
        return ChannelDecision(True, "warm_lead_sms_thread")

    @staticmethod
    def should_mark_warm_lead(reply_intent: str) -> bool:
        return reply_intent == "schedule"
