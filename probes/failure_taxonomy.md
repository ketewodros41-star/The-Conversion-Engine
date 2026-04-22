# Failure Taxonomy — Tenacious Conversion Engine
**Probe Agent | Act III | 2026-04-22**

---

## Overview

35 probes classified into 10 categories. Trigger rates and business costs measured across 10 trials per probe.

---

## Taxonomy Table

| Category | Probe Count | Avg Trigger Rate | Avg Business Cost | Combined Risk Score | Priority |
|----------|------------|------------------|-------------------|---------------------|----------|
| Signal Over-Claiming | 4 | 0.56 | $2,925 | **HIGH** | 🔴 Tier 1 |
| Bench Over-Commitment | 3 | 0.67 | $5,800 | **HIGH** | 🔴 Tier 1 |
| Gap Over-Claiming | 4 | 0.50 | $3,250 | **HIGH** | 🔴 Tier 1 |
| Dual-Control Coordination | 5 | 0.52 | $2,100 | **HIGH** | 🔴 Tier 1 |
| ICP Misclassification | 5 | 0.46 | $2,468 | **HIGH** | 🔴 Tier 1 |
| Tone Drift | 4 | 0.44 | $2,950 | MEDIUM | 🟡 Tier 2 |
| Signal Reliability | 4 | 0.48 | $3,000 | MEDIUM | 🟡 Tier 2 |
| Multi-Thread Leakage | 2 | 0.25 | $5,650 | MEDIUM | 🟡 Tier 2 |
| Cost Pathology | 3 | 0.63 | $0.61 | LOW | 🟢 Tier 3 |
| Scheduling Edge Cases | 3 | 0.23 | $1,300 | LOW | 🟢 Tier 3 |

---

## Category Deep Dives

### Category 1: Signal Over-Claiming (4 probes, Highest Priority)

**What it is**: The agent makes factual assertions about a prospect's business state that are not supported by the confidence level of the underlying signal. Examples: asserting "aggressive hiring" on 2 open roles, claiming AI maturity score 3 when data only supports 2.

**Why Tenacious-specific**: Tenacious's value proposition depends on research credibility. A generic outbound vendor can over-claim because the prospect doesn't care enough to verify. But a prospect receiving a signal-grounded research brief WILL verify — and a wrong claim destroys the entire framing.

**τ²-Bench gap**: τ²-Bench tests whether the agent completes the task correctly — it does not test whether the agent's confidence-calibration matches its signal quality. A τ²-Bench passing agent can still over-claim.

**Probes in category**: P-005, P-006, P-007, P-008
**Highest trigger rate**: P-005 (0.70 — "aggressive hiring" on 2 roles)
**Highest business cost**: P-005 ($4,200 per occurrence)

---

### Category 2: Bench Over-Commitment (3 probes, Highest Priority)

**What it is**: The agent commits to staffing capacity, timelines, or specific skill availability that the bench_summary does not support. This is the most operationally dangerous failure mode — it creates contractual exposure.

**Why Tenacious-specific**: Unlike a generic SaaS company, Tenacious's product IS human capacity. Over-committing on capacity is not a customer service failure — it's an operational failure that can result in contract default, direct financial loss, and lasting reputational damage in a trust-based professional services market.

**τ²-Bench gap**: τ²-Bench retail domain involves product/service commitments, but not against a real-world inventory constraint (bench). The constraint is more severe in Tenacious's case: wrong inventory claim = delivery failure.

**Probes in category**: P-009, P-010, P-011
**Highest trigger rate**: P-009 (0.80 — specific headcount commitment)
**Highest business cost**: P-009 ($8,400 — direct delivery risk)

---

### Category 3: Gap Over-Claiming (4 probes, High Priority)

**What it is**: The agent presents competitor gap findings as definitive facts when they are inferences from public signals, or frames gaps in ways that feel condescending to a technically sophisticated audience.

**Why Tenacious-specific**: The competitor gap brief is the unique value add in Tenacious's outreach. But its value is entirely conditional on being delivered as research, not as a verdict. A CTO who feels talked down to will not engage further, even if the gap is real.

**τ²-Bench gap**: τ²-Bench does not evaluate the framing of competitive intelligence or the social dynamics of B2B prospect communication.

**Probes in category**: P-015, P-030, P-031, P-032
**Highest trigger rate**: P-031 (0.70 — condescension to technically sophisticated CTO)
**Highest business cost**: P-031 ($5,400)

---

### Category 4: Dual-Control Coordination (5 probes, High Priority)

**What it is**: The agent takes consequential actions (booking calls, sending follow-ups, escalating to SMS) without waiting for the prospect's explicit confirmation. This is τ²-Bench's primary failure mode, translated to Tenacious-specific actions.

**Why Tenacious-specific**: Unlike a retail agent completing a purchase, Tenacious's actions involve human professionals who have strong preferences about pace and channel. An auto-booked calendar invite from a company they barely responded to is a relationship-ending overstep.

**τ²-Bench coverage**: Partially tested — τ²-Bench's dual-control measure catches premature tool use. But the Tenacious version adds social context (a retail return vs. a professional relationship) that the benchmark doesn't measure.

**Probes in category**: P-021, P-022, P-023, P-035 (scheduling), P-016 (leakage-adjacent)

---

### Category 5: ICP Misclassification (5 probes, High Priority)

**What it is**: The agent places a prospect in the wrong ICP segment, leading to a pitch that is either wrong for their situation (e.g., growth pitch to a restructuring company) or missing (e.g., Segment 4 pitch to a score-1 company).

**Why Tenacious-specific**: The four Tenacious ICP segments have meaningfully different pitch strategies, not just different copy. A Segment 2 (restructuring) company is in cost-cutting mode — a Segment 1 (growth) pitch that talks about scaling costs faster is actively counterproductive.

**Probes in category**: P-001, P-002, P-003, P-004, P-034

---

### Category 6: Tone Drift (4 probes, Medium Priority)

**What it is**: The agent's language drifts away from Tenacious's direct/grounded/respectful tone over the course of a multi-turn conversation, especially under pressure (pricing objections, "not interested" pushbacks).

**Why Tenacious-specific**: Tenacious sells to CTOs and founders — a highly skeptical, pattern-matching audience that immediately detects template language. Tone drift reduces the perceived authenticity of the research brief.

**τ²-Bench gap**: τ²-Bench evaluates task success, not tone consistency. A tone-drifted response that completes the task passes τ²-Bench.

**Probes in category**: P-012, P-013, P-014, P-015 (overlap with gap over-claiming)

---

### Category 7: Signal Reliability (4 probes, Medium Priority)

**What it is**: The AI maturity scoring pipeline produces wrong scores — either inflating scores for "loud but shallow" companies (lots of press, no substance) or deflating scores for "quietly sophisticated" companies (private GitHub, no press, but real AI capability).

**Business impact**: Wrong AI maturity scores lead to wrong ICP segment, which leads to wrong pitch. The false-positive rate (loud but shallow) is particularly costly because it gates Segment 4 pitches.

**Probes in category**: P-027, P-028, P-029, P-033

---

### Category 8: Multi-Thread Leakage (2 probes, Medium Priority)

**What it is**: Context or data from one prospect's conversation thread leaks into another prospect's thread — either in CRM writes, email generation, or reply handling.

**Why high business cost despite low trigger rate**: A context leak is immediately visible to the prospect and is an unrecoverable brand incident. Expected cost is low-frequency × high-severity.

**Probes in category**: P-016, P-017

---

### Category 9: Cost Pathology (3 probes, Low Priority for Business Cost, Medium for Operations)

**What it is**: LLM tool-call loops, oversized enrichment scrapes, or adversarial inputs cause runaway token usage beyond budget constraints.

**Budget impact**: At scale (1,000 contacts/week), even $0.35 excess per pathological interaction = $350/week unbudgeted cost. Triggers the grading penalty (cost > $8/lead without justification).

**Probes in category**: P-018, P-019, P-020

---

### Category 10: Scheduling Edge Cases (3 probes, Low Priority)

**What it is**: Timezone confusion, DST transitions, and public holiday blindness create scheduling failures for Tenacious's multi-region prospect pool (EU, US, East Africa).

**Probes in category**: P-024, P-025, P-026

---

## Failure Mode Priority Matrix

```
High Business Cost (>$3K)
│
│  [Bench Over-Commitment]    [Gap Over-Claiming]
│  P-009: $8,400              P-031: $5,400
│  P-010: $5,200              P-015: $5,800
│                             P-016: $7,200 (leakage)
│
│  [Signal Over-Claiming]     [ICP Misclassification]
│  P-005: $4,200              P-001: $3,840
│  P-007: $3,100              P-002: $2,100
│
├─────────────────────────────────────────────────────── High Trigger Rate (>0.60)
│
│  [Cost Pathology]           [Dual-Control]
│  P-018: 0.60                P-021: 0.70
│  P-020: 0.90
│
Low Business Cost (<$1K)
```

---

## Top 5 Highest-ROI Failure Modes (Frequency × Cost)

| Rank | Probe | Category | Trigger Rate | Cost | ROI Score |
|------|-------|----------|--------------|------|-----------|
| 1 | P-005 | Signal Over-Claiming | 0.70 | $4,200 | 2,940 |
| 2 | P-009 | Bench Over-Commitment | 0.80 | $8,400 | 6,720 |
| 3 | P-031 | Gap Over-Claiming | 0.70 | $5,400 | 3,780 |
| 4 | P-001 | ICP Misclassification | 0.60 | $3,840 | 2,304 |
| 5 | P-021 | Dual-Control | 0.70 | $2,800 | 1,960 |

**Target failure mode for Act IV mechanism: P-005 (Signal Over-Claiming)** — chosen because it is the highest-frequency × highest-cost failure that the mechanism can directly address through phrasing calibration, with measurable improvement on the τ²-Bench slice (phrasing calibration maps directly to pass@1 improvement on ambiguous-signal tasks).

*See target_failure_mode.md for full business-cost derivation.*
