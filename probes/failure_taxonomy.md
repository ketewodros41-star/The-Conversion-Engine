# Failure Taxonomy - Tenacious Conversion Engine
**Probe Agent | Act III | 2026-04-24**

---

## Overview

35 probes classified into 10 categories. Every probe in `probe_library.md` is mapped exactly once below. Category trigger rates are the arithmetic mean of member-probe trigger rates; business cost is the arithmetic mean of member-probe business-cost estimates.

---

## Taxonomy Table

| Category | Probe Count | Avg Trigger Rate | Avg Business Cost | Shared Failure Pattern |
|----------|------------:|-----------------:|------------------:|------------------------|
| Signal Over-Claiming | 4 | 0.56 | $2,925 | Agent states research findings more strongly than the underlying evidence supports. |
| Bench Over-Commitment | 3 | 0.67 | $5,800 | Agent promises staffing capacity or timelines without delivery-safe inventory evidence. |
| Gap Over-Claiming | 3 | 0.52 | $3,600 | Agent turns competitor research into verdicts rather than evidence-backed hypotheses. |
| Dual-Control Coordination | 4 | 0.53 | $2,125 | Agent takes a consequential next step before the prospect has explicitly consented. |
| ICP Misclassification | 5 | 0.47 | $1,868 | Agent chooses the wrong segment and therefore the wrong commercial frame. |
| Tone Drift | 4 | 0.44 | $2,950 | Agent drifts away from Tenacious's direct, respectful, peer-to-peer tone. |
| Signal Reliability | 4 | 0.48 | $3,125 | Upstream signal interpretation is wrong even before phrasing or channel logic. |
| Multi-Thread Leakage | 2 | 0.25 | $5,650 | State or context leaks across contacts or conversations. |
| Cost Pathology | 3 | 0.63 | $0.61 | Tool loops or oversized inputs create avoidable operating cost spikes. |
| Scheduling Edge Cases | 3 | 0.23 | $967 | Calendar and timezone handling fails across the US, EU, and East Africa. |

---

## Category Deep Dives

### 1. Signal Over-Claiming

Description: factual claims outrun signal confidence, especially on hiring velocity, AI maturity, or inferred gaps.

Aggregate trigger rate: `0.56`

Probes in category: `P-005, P-006, P-007, P-008`

### 2. Bench Over-Commitment

Description: the agent commits to staffing, specialization, or start-date claims that Tenacious may not be able to honor.

Aggregate trigger rate: `0.67`

Probes in category: `P-009, P-010, P-011`

### 3. Gap Over-Claiming

Description: competitor-gap research is presented as a judgment against the prospect instead of a grounded sector comparison.

Aggregate trigger rate: `0.52`

Probes in category: `P-030, P-031, P-032`

### 4. Dual-Control Coordination

Description: the agent acts before the prospect explicitly confirms the next step, especially around booking and SMS escalation.

Aggregate trigger rate: `0.53`

Probes in category: `P-021, P-022, P-023, P-035`

### 5. ICP Misclassification

Description: upstream segmentation logic misreads the prospect's actual commercial situation.

Aggregate trigger rate: `0.47`

Probes in category: `P-001, P-002, P-003, P-004, P-034`

### 6. Tone Drift

Description: tone degrades under pressure and starts sounding templated, defensive, or condescending.

Aggregate trigger rate: `0.44`

Probes in category: `P-012, P-013, P-014, P-015`

### 7. Signal Reliability

Description: the signal extraction and scoring layer itself is wrong, including false positives and false negatives.

Aggregate trigger rate: `0.48`

Probes in category: `P-027, P-028, P-029, P-033`

### 8. Multi-Thread Leakage

Description: conversation or CRM context from one contact leaks into another thread.

Aggregate trigger rate: `0.25`

Probes in category: `P-016, P-017`

### 9. Cost Pathology

Description: the system spends too much on avoidable tool calls, long-context handling, or repeated scheduling work.

Aggregate trigger rate: `0.63`

Probes in category: `P-018, P-019, P-020`

### 10. Scheduling Edge Cases

Description: timezone, DST, and holiday handling breaks the booking experience for a multi-region prospect base.

Aggregate trigger rate: `0.23`

Probes in category: `P-024, P-025, P-026`

---

## Coverage Check

- Probe IDs covered: `P-001` through `P-035`
- Orphan probes: `0`
- Duplicate probe assignments: `0`
- Highest ROI category by cost x frequency: `Bench Over-Commitment`
- Targetable category selected for Act IV mechanism: `Signal Over-Claiming`

---

## Why P-005 Still Wins

`P-009` has the single highest expected business cost, but it is not the best Act IV target because the root cause is commitment policy and human handoff, not phrasing calibration. `P-005` remains the best mechanism target because:

1. It is frequent.
2. It is expensive enough to matter.
3. It is directly reducible by confidence-aware phrasing.
4. It maps to an evaluable change in the current benchmark setup.

See `target_failure_mode.md` for the full business-cost arithmetic and alternative comparison.
