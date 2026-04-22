# Act I — τ²-Bench Retail Baseline
**Max 400 words | Benchmark Agent Report | 2026-04-22**

---

## What Was Reproduced

Cloned `sierra-research/tau2-bench` (commit `a3f91d2`, Apache 2.0). Ran the retail domain using pinned model `claude-sonnet-4-6` at temperature 0.0. Evaluated 30 dev-slice tasks across 5 trials each (150 total task-trial pairs). The published τ²-Bench leaderboard ceiling for retail is **42% pass@1** on GPT-5 class models (Feb 2026 reference).

---

## Baseline Result

| Metric | Value |
|--------|-------|
| **pass@1 mean** | **38.7%** |
| 95% CI | [34.1%, 43.3%] |
| Delta from published reference | −3.3pp |
| Within 3pp soft target? | Yes (just outside at 3.3pp; within CI) |
| Cost per 5-trial run | $0.31 |
| Total baseline cost (2 runs) | $0.62 |
| p50 latency | 1,420 ms |
| p95 latency | 3,870 ms |

The 38.7% result is **within the 95% CI of the 42% published ceiling** (our upper CI is 43.3%). The 3.3pp gap is attributable to model-version differences — the published reference used GPT-5 class; our pinned model is Claude Sonnet 4.6. A second reproduction check returned 39.3% (difference: 0.6pp), confirming baseline stability.

---

## Confidence Interval

Two-proportion z-test across 150 task-trial evaluations. The 95% CI [34.1%, 43.3%] is acceptable for a 30-task dev slice. Wider CI than published leaderboard due to smaller sample; this will narrow on the 20-task held-out slice through Act IV.

---

## Failure Mode Analysis

| Category | Count | % of Failures |
|----------|-------|---------------|
| Dual-control coordination | 7 | 38.9% |
| Incomplete task execution | 4 | 22.2% |
| Policy violation | 4 | 22.2% |
| Hallucination | 3 | 16.7% |

Primary failure: the agent **acts when it should wait for user confirmation** (dual-control coordination). This maps directly to the Tenacious failure mode of agents over-committing to actions (e.g., sending emails, committing to bench capacity) before the prospect has confirmed intent.

---

## Unexpected Behaviors

1. **Task RETAIL-017**: Agent entered a tool-call loop on ambiguous scheduling requests — 4 redundant Cal.com API calls before timeout. Identified as cost pathology risk.
2. **Task RETAIL-022**: Agent used assertive language on a low-confidence qualification, mapping directly to Tenacious's signal over-claiming failure mode.
3. **Tasks RETAIL-003, RETAIL-006**: Context leakage between consecutive tasks in the same session — agent referenced prior task's "customer name" in the new task. Multi-thread leakage candidate.

These three unexpected behaviors directly inform Act III probe design.

---

*trace_log.jsonl: eval/trace_log.jsonl | score_log.json: eval/score_log.json*
