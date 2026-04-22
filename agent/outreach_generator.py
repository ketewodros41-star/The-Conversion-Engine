"""
Tenacious Conversion Engine — Outreach Generator
Generates signal-grounded outbound emails, reply handlers, and qualification flows.
Preserves Tenacious tone from style_guide.md.
"""

import os
from typing import Optional
import anthropic
import structlog

log = structlog.get_logger()

TENACIOUS_STYLE_GUIDE = """
Tenacious tone markers (from style_guide.md):
1. DIRECT: Short sentences. No fluff. Get to the point in the first line.
2. GROUNDED: Every claim references a specific, verifiable signal. No vague assertions.
3. RESPECTFUL: Never condescending. Never assume the prospect doesn't know their market.
4. HONEST UNDER UNCERTAINTY: Low-confidence signals are phrased as questions, not assertions.
5. HUMAN: Reads like a thoughtful person wrote it, not a template.
6. NEVER: 'offshore' or 'outsourcing' in subject lines. Never 'scale faster than your competitors'.
7. ACV REFERENCE: Don't quote specific pricing. Route deeper pricing to human.
8. CHANNEL: Email is for cold outreach. SMS only for scheduling from warm leads who replied.
"""

SEGMENT_TEMPLATES = {
    "segment_1": {
        "subject_high_maturity": "AI team scaling at {company} — quick context",
        "subject_low_maturity": "{company} first AI function — worth 30 min?",
        "opening_high": "You closed a {round} in {month} and your open engineering roles have roughly {velocity} since then — the typical bottleneck at that stage is recruiting capacity, not budget.",
        "opening_low": "You raised a {round} {days_ago} days ago. Most companies at that stage start thinking about standing up a first dedicated AI function in months 4–6 — this is about that.",
    },
    "segment_2": {
        "subject": "Engineering capacity post-restructure at {company}",
        "opening": "Post-restructure, a lot of teams find they've right-sized the headcount but still have the same delivery targets. The question is usually how to maintain output without the same burn.",
    },
    "segment_3": {
        "subject": "Intro — new CTO at {company}",
        "opening": "Congratulations on the new role. New engineering leaders usually have a 60-90 day window to reassess vendor and team mix before the current state calcifies. Worth a quick call?",
    },
    "segment_4": {
        "subject": "{company} ML platform — 30 min?",
        "opening": "Your public signals — GitHub activity on inference optimization, {ai_adjacent_pct}% of engineering roles AI-adjacent — suggest you're building out ML platform capacity at pace. Worth a conversation about where teams at your stage typically hit the wall.",
    },
    "exploratory": {
        "subject": "{company} + Tenacious — quick intro",
        "opening": "Came across {company} while researching the {sector} space. Tenacious works with engineering teams that are scaling fast or building AI-adjacent systems. Not sure yet if there's a fit, but thought it worth a quick check.",
    }
}


class OutreachGenerator:
    """Generates personalized, signal-grounded outbound emails for Tenacious ICP segments."""

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def _build_system_prompt(self) -> str:
        return f"""You are writing outbound email for Tenacious Consulting and Outsourcing.

{TENACIOUS_STYLE_GUIDE}

Rules:
- Every factual claim must be grounded in the provided hiring_signal_brief
- If a signal has confidence < 0.75, phrase as a question, not an assertion
- Never claim 'aggressive hiring' if fewer than 5 open roles
- Never commit to bench capacity — say 'we have engineers available' not specific counts
- Never mention competitors by name in outreach emails
- Keep emails under 180 words
- Mark all output as DRAFT in metadata
- Do not fabricate additional case studies beyond those in seed materials"""

    def generate_outbound_email(
        self,
        prospect: dict,
        hiring_brief: dict,
        competitor_brief: dict,
        segment: str,
        bench_available: bool,
        live_mode: bool = False,
    ) -> dict:
        """Generate signal-grounded outbound email for a prospect."""

        signals = hiring_brief.get("signals", {})
        funding = signals.get("funding_event", {})
        jobs = signals.get("job_post_velocity", {})
        ai_maturity = signals.get("ai_maturity", {})

        # Build context from briefs
        context = self._build_email_context(prospect, signals, competitor_brief, segment)

        # Use Claude to generate the email
        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=400,
                system=self._build_system_prompt(),
                messages=[{
                    "role": "user",
                    "content": f"""Generate a signal-grounded outbound email for this prospect.

PROSPECT: {prospect['company_name']}
CONTACT: {prospect['contact_name']}, {prospect['contact_title']}
ICP SEGMENT: {segment}
BENCH AVAILABLE: {bench_available}

SIGNAL CONTEXT:
{context}

COMPETITOR GAP HOOK (use at most ONE gap, the most concrete one):
{self._get_best_gap(competitor_brief)}

Generate:
1. Subject line
2. Email body (under 180 words)
3. Mark confidence-limited claims appropriately

Format as JSON: {{"subject": "...", "body": "...", "word_count": N, "confidence_notes": [...]}}"""
                }]
            )

            import json
            content = response.content[0].text
            # Parse JSON from response
            start = content.find('{')
            end = content.rfind('}') + 1
            if start >= 0 and end > start:
                email_data = json.loads(content[start:end])
            else:
                raise ValueError("No JSON in response")

        except Exception as e:
            log.error("email_generation_failed", error=str(e), company=prospect['company_name'])
            # Fallback to template
            template = SEGMENT_TEMPLATES.get(segment, SEGMENT_TEMPLATES["exploratory"])
            email_data = {
                "subject": template.get("subject", template.get("subject_high_maturity", "")).format(
                    company=prospect['company_name'],
                    round=funding.get("round_type", "recent round"),
                    month="recently",
                    velocity="grown",
                    days_ago=funding.get("days_since_close", "recently"),
                    ai_adjacent_pct=int(jobs.get("ai_adjacent_roles", 0) /
                                        max(jobs.get("engineering_roles", 1), 1) * 100),
                    sector=prospect.get("industry", "tech"),
                ),
                "body": f"Hi {prospect['contact_name'].split()[0]},\n\n{template.get('opening', template.get('opening_high', '')).format(round=funding.get('round_type', 'recent round'), month='recently', velocity='grown', days_ago=str(funding.get('days_since_close', 'recently')), ai_adjacent_pct='many', company=prospect['company_name'], sector=prospect.get('industry', 'tech'))}\n\nTenacious works with engineering teams that are scaling at pace. Worth 30 minutes?\n\n—\nTenacious Consulting and Outsourcing\n[DRAFT]",
                "word_count": 60,
                "confidence_notes": ["Template fallback — AI generation failed"],
            }

        email_data["metadata"] = {
            "is_draft": True,
            "variant": segment,
            "crunchbase_id": prospect.get("crunchbase_id"),
            "is_synthetic": prospect.get("is_synthetic", True),
            "live_mode": live_mode,
        }

        return email_data

    def _build_email_context(self, prospect: dict, signals: dict,
                              competitor_brief: dict, segment: str) -> str:
        lines = []
        funding = signals.get("funding_event", {})
        jobs = signals.get("job_post_velocity", {})
        ai = signals.get("ai_maturity", {})

        if funding.get("present"):
            lines.append(f"- Funding: {funding.get('round_type')} ${funding.get('amount_usd', 0)/1e6:.0f}M, {funding.get('days_since_close')} days ago (confidence: {funding.get('confidence', 0):.0%})")

        role_count = jobs.get("total_open_roles", 0)
        if role_count >= 5:
            lines.append(f"- Job post velocity: {role_count} open roles, {jobs.get('ai_adjacent_roles', 0)} AI-adjacent (confidence: {jobs.get('confidence', 0):.0%})")
        elif role_count > 0:
            lines.append(f"- Job posts: {role_count} open roles [LOW COUNT: do not assert 'aggressive hiring']")

        lines.append(f"- AI maturity score: {ai.get('score', 0)}/3 (confidence: {ai.get('confidence', 0):.0%} — {ai.get('confidence_tier', 'low')})")

        return "\n".join(lines)

    def _get_best_gap(self, competitor_brief: dict) -> str:
        gaps = competitor_brief.get("identified_gaps", [])
        high_conf_gaps = [g for g in gaps if g.get("confidence", 0) >= 0.80]
        if high_conf_gaps:
            g = high_conf_gaps[0]
            return f"{g['gap_name']}: {g['business_implication']}"
        return "No high-confidence gap identified — do not assert competitor comparison"

    def classify_reply_intent(self, email_body: str) -> str:
        """Classify inbound reply intent: schedule, qualify, object, unsubscribe."""
        body_lower = email_body.lower()

        if any(w in body_lower for w in ["unsubscribe", "remove me", "stop emailing", "not interested"]):
            return "unsubscribe"
        if any(w in body_lower for w in ["schedule", "book", "call", "meeting", "calendar", "available", "time"]):
            return "schedule"
        if any(w in body_lower for w in ["tell me more", "how does", "what do you", "curious", "interesting"]):
            return "qualify"
        return "qualify"  # Default: continue qualification

    def generate_scheduling_reply(self, contact: dict, slots: list, channel: str) -> dict:
        """Generate scheduling reply for warm lead who wants to book a call."""
        slot_list = "\n".join([f"• {s['display']}" for s in slots[:3]])
        name = contact.get("firstname", "there")

        return {
            "body": f"""Hi {name},

Great — happy to connect. A few times that work for a 30-minute call:

{slot_list}

Any of these work? Or reply with your preferred time and I'll find a slot.

—
Tenacious Consulting and Outsourcing
[DRAFT]""",
            "sms_follow_up": f"Quick follow-up on scheduling — do any of these work? {slots[0]['display'] if slots else 'Let me know your availability'}"
        }

    def generate_qualification_reply(self, contact: dict, email_body: str) -> dict:
        """Generate qualification follow-up for a prospect asking for more info."""
        name = contact.get("firstname", "there")
        return {
            "body": f"""Hi {name},

Happy to share more. A few questions that help me give you a useful answer:
1. What's the main constraint right now — is it recruiting speed, specific skills, or cost structure?
2. What does your current engineering team composition look like?
3. What's your timeline for the next hire?

Worth 20 minutes to talk through? I can adjust to what's most useful.

—
Tenacious Consulting and Outsourcing
[DRAFT]""",
        }
