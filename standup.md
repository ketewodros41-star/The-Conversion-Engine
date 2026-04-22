# Daily Standup — Tenacious Conversion Engine
**Date: 2026-04-22 | Author: Kidus Gashaw**

---

## 1. What is the specific 'Hiring Signal' trigger you've chosen to target?

The primary trigger is **job-post velocity combined with a funding event within 180 days** — specifically: a company that closed a **Series A or B** ($5M–$30M) in the last 6 months AND has seen its open engineering roles grow by **≥5 new postings in the last 60 days**, with at least 2 of those being AI-adjacent (ML Engineer, LLM Infrastructure, Data Platform Engineer).

The logic: fresh funding means budget is confirmed. A sudden spike in engineering job posts means in-house recruiting can't keep up with the post-funding hiring plan. That gap — budget available, recruiting bottleneck real, clock ticking — is the exact moment Tenacious's value proposition lands.

**Why this signal specifically:**
- It's **verifiable in under 60 seconds** on the prospect's own Wellfound or LinkedIn page, which means the claim in the outreach email is hard to dispute
- It maps cleanly to **Segment 1** (recently-funded startups) — the highest-priority ICP segment
- It has a built-in confidence threshold: if fewer than **5 open roles** exist, the agent does NOT assert "aggressive hiring" — it asks instead. This was the highest-ROI failure mode in adversarial probing (probe P-005, trigger rate 0.70 pre-fix)

**Secondary trigger (Segment 3):** A new CTO or VP Engineering appointed in the last **90 days**, detected from Crunchbase people data. New engineering leaders reassess vendor and offshore mix in their first 6 months — this is a narrow but high-conversion window.

**The AI Maturity score (0–3)** runs in parallel for all prospects and gates which pitch language gets used:
- Score ≥ 2 → eligible for Segment 4 (ML platform / agentic systems consulting pitch)
- Score 1 → Segment 1 language shifts to "stand up your first AI function"
- Score 0 → Segment 4 pitch is blocked entirely

---

## 2. Walk us through your Prompt Chain — single massive prompt or decoupled Researcher + Closer?

**Decoupled. Two distinct agents with a structured handoff.**

### Agent 1 — The Researcher (`enrichment.py` + `icp_classifier.py`)

Runs **before any LLM call**. This is mostly Python logic, not prompting:

```
Crunchbase ODM lookup
    → Funding signal detection (date check, round type)
    → Job-post scraping (Playwright, respects robots.txt)
    → Layoffs.fyi check
    → Leadership change detection
    → AI maturity scoring (0–3, rule-based weighted scoring)
    → ICP classification with confidence score
    → Bench-to-brief match check
```

Output: a structured `hiring_signal_brief.json` and `competitor_gap_brief.json` with **per-signal confidence scores** attached to every field. No LLM is involved here — pure data pipeline. This keeps the research step cheap, fast, and auditable.

### The Handoff — SCAP v2 (Signal-Confidence-Aware Phrasing)

Before the Closer agent runs, the Researcher's output is processed through a **confidence gate** that converts signal data into phrasing instructions:

```
funding_event.confidence = 0.97  →  "ASSERT as fact"
job_velocity.confidence  = 0.52  →  "QUESTION — ask, don't assert"
ai_maturity.confidence   = 0.78  →  "HEDGE — use 'appears', 'suggests'"
```

These instructions are injected into the Closer agent's system prompt dynamically. The Closer never sees raw confidence numbers — it sees explicit phrasing rules. This is the Act IV mechanism that lifted pass@1 from 38.7% to 46.1%.

### Agent 2 — The Closer (`outreach_generator.py`)

A single LLM call (Claude Sonnet 4.6) that receives:
- The prospect's segment classification
- The signal context (already confidence-filtered)
- The best competitor gap (highest-confidence gap only)
- The phrasing instruction block from SCAP v2
- Hard constraints: under 180 words, no specific headcount commitments, no competitor names, no "offshore" in subject lines

Output: subject line + email body, returned as JSON. If generation fails, a template fallback fires — the system never goes silent.

### Why decoupled?

| Concern | Single Prompt | Decoupled |
|---------|--------------|-----------|
| Cost | One call but large context | Researcher is free (no LLM), Closer is small and focused |
| Auditability | Hard to trace which signal drove which claim | Every claim in the email traces back to a specific signal and confidence score |
| Failure isolation | Research failure = silent hallucination | Research failure = explicit error before any email is generated |
| Prompt drift | Researcher logic lives in a 2,000-token system prompt | Researcher logic lives in typed Python — testable, versionable, debuggable |

The one trade-off: two-step latency. The enrichment pipeline adds ~3.9 seconds before the LLM call. At the volume Tenacious operates (60 emails/week, not 60,000), this is invisible.

---

*References: `agent/enrichment.py`, `agent/icp_classifier.py`, `agent/outreach_generator.py`, `method/method.md`*
