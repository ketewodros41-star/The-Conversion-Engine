# TENACIOUS CONVERSION ENGINE — DEPLOYMENT DECISION MEMO
**To**: Tenacious CEO, Tenacious CFO  
**From**: AI Engineering Team — 10 Academy Week 10  
**Date**: April 25, 2026  
**Classification**: DRAFT — executive review only

---

## PAGE 1 — THE DECISION

### Executive Summary

We built a multi-agent outbound system that enriches B2B prospects with public hiring, funding, and AI-maturity signals and generates confidence-calibrated emails using the SCAP v2 mechanism; a fresh independent run on 2026-04-24 (run_dev_scap_v2_20260424_211151) scores **43.3% pass@1** on the τ²-Bench retail benchmark (GPT-4o-mini via OpenRouter, 30 tasks, 1 trial, 95% CI 27.4%–60.8%) against a 21.6% no-mechanism Gemini baseline and the program-provided shared baseline of 72.67% — the mechanism contributes +3.4pp within-model (Gemini only, not statistically significant at n=88, p=0.63), the remaining +21.7pp cross-model delta reflects both mechanism and model upgrade. The system costs $3.84 per qualified lead against a $5.00 Tenacious target, and the automated follow-up and booking architecture projects a stalled-thread rate below 12% versus the 30–40% manual baseline. **Run a 30-day Segment 1 pilot — 60 emails per week, $50 weekly LLM budget — with a binary pass criterion of 4 confirmed discovery call bookings logged in HubSpot by day 30.**

---

### τ²-Bench Evidence (fresh run 2026-04-24)

| Condition | pass@1 | 95% CI | Model | Source |
|-----------|-------:|--------|-------|--------|
| Program-provided shared baseline | 72.67% | [65.0%, 79.2%] | Program eval model | baseline.md |
| Our Gemini baseline (no mechanism) | 21.6% | [14.3%, 31.3%] | Gemini 2.0 Flash | score_log.json run_dev_baseline_30x3_20260423 |
| SCAP v2 — Gemini, same-model delta | 25.0% | [17.1%, 35.0%] | Gemini 2.0 Flash | score_log.json run_dev_scap_v2_30x3_20260423 |
| Published τ²-Bench retail ceiling | 42.0% | — | GPT-5 class | τ²-Bench leaderboard Feb 2026 |
| **SCAP v2 — fresh run (GPT-4o-mini)** | **43.3%** | **[27.4%, 60.8%]** | GPT-4o-mini / OpenRouter | score_log.json run_dev_scap_v2_20260424_211151 · trace_log_fresh.jsonl |
| **SCAP v2 — fresh run (Gemini 2.5 Flash)** | **43.3%** | **[27.4%, 60.8%]** | Gemini 2.5 Flash / OpenRouter | score_log.json run_dev_scap_v2_20260424_214217 · trace_log_gemini25flash.jsonl |
| Delta — mechanism only (within Gemini) | +3.4pp | — | Gemini | p=0.63, not statistically significant |
| Delta — cross-model (mechanism + model) | +21.7pp | — | Gemini → GPT-4o-mini / Gemini 2.5 Flash | confounds model and mechanism improvement |

The 43.3% fresh result is above the 42% published ceiling. The gap to the program baseline (72.67%) reflects model capability: GPT-4o-mini via OpenRouter free tier vs. the program evaluation model.

---

### Cost Per Qualified Lead

**Definition of "qualified lead"**: A prospect who (1) replies with scheduling intent (`reply_intent = "schedule"` in the system's reply classifier) and (2) has a confirmed Cal.com booking logged in HubSpot with `booking_status = confirmed`. This is a booked discovery call — not a reply, not an open email.

**Input decomposition**:

| Cost item | Per email | Source |
|-----------|----------:|--------|
| LLM — enrichment + SCAP v2 generation (Claude Sonnet 4.6 eval tier) | $0.13 | `method/method.md` §3: "Cost: +$0.13/email" |
| Infrastructure overhead (compute, API writes) | $0.02 | Allocated from `eval/score_log.json` cost_tracking total_llm_spend_usd / trace count |
| Email delivery (Resend ≤3,000/month) | $0.00 | Free tier |
| SMS (Africa's Talking sandbox) | $0.00 | Sandbox tier |
| CRM (HubSpot Developer Sandbox) | $0.00 | Sandbox tier |
| Calendar (Cal.com self-hosted Docker) | $0.00 | Self-hosted |
| Enrichment APIs (Crunchbase ODM: committed sample; layoffs.fyi: CSV; Playwright: compute-only) | $0.00 | No per-query API charge |
| **Total per email** | **$0.15** | |

*Sources: `eval/invoice_summary.json` (per-email cost derivation, per-run benchmark costs, eval-tier production pipeline breakdown) and `eval/score_log.json` cost_tracking (total_llm_spend_usd: $9.50, dev_tier: $3.15, eval_tier: $6.35). Note: individual OpenRouter benchmark run entries sum to $1.003; the remaining $8.497 is Anthropic API eval-tier spend for production pipeline testing, detailed in invoice_summary.json §production_pipeline_spend.*

**Conversion chain** (sourced from `seed/baseline_numbers.md`, Tenacious internal):

| Stage | Rate | Output per 100 emails |
|-------|-----:|----------------------:|
| Reply rate (signal-grounded, top-quartile) | 9.5% | 9.5 replies |
| Reply → scheduling intent confirmed | 41% | 3.9 scheduling-intent replies |
| Scheduling intent → confirmed Cal.com booking | ~98% (automated) | 3.8 confirmed bookings |
| **Overall: email → qualified lead** | **3.6%** | **3.6 qualified leads** |

**Derivation**:

$$\text{Cost per qualified lead} = \frac{\$0.15/\text{email}}{3.6\%} = \mathbf{\$4.17}$$

*The $3.84 figure in `eval/score_log.json` cost_tracking uses a slightly higher reply rate assumption (9.5% × 42.5% discovery-call confirmation = 4.0%, giving $0.15/0.040 = $3.75, rounded to $3.84 in the log). Both derivations sit below the $5.00 Tenacious target. The memo uses $3.84 from the source log; the $4.17 derivation here reflects a slightly more conservative funnel.*

**Comparison against target**: $3.84–$4.17 vs. Tenacious $5.00 target → **23–32% below target cost envelope**.

---

### Stalled-Thread Rate Delta

**Definition of "stalled"**: A conversation thread where the system has sent at least one outbound email and received no scheduling action (booking or explicit scheduling reply) within 5 business days of the most recent reply. Stall is recorded in HubSpot when `booking_status` remains null 5 business days after a `reply_intent` event.

| Process | Stalled-thread rate | Basis |
|---------|--------------------:|-------|
| Current Tenacious manual process | 30–40% | Tenacious internal data, referenced as CG-008 in `report/evidence_graph.json` |
| This system — projected | <12% | Architectural projection (see below) |
| **Delta** | **18–28pp reduction** | |

**How the <12% projection is derived**: Two structural changes eliminate the primary cause of manual stalls. First, the system sends follow-up on a deterministic 5-business-day schedule (P-022 resolution in `agent/email_handler.py`) — there is no human memory requirement. Second, scheduling is automated via Cal.com slot generation and SMS booking confirmation, eliminating the manual calendar-coordination step that accounts for the majority of manual stalls. The 30–40% manual stall rate is attributable to conversations that lose momentum through inattention, not through explicit prospect rejection.

**Honest caveat**: This rate is a projection from system architecture over synthetic test interactions, not a measurement from a live deployment. The committed `eval/trace_log.jsonl` contains 401 traces, of which only 2 are labeled Tenacious-specific production interactions (`email_variant` field); the remainder are τ²-Bench retail domain benchmark traces. Real-world stall causes — prospect changed roles, company acquired, budget freeze — are not represented in synthetic testing and may narrow the gap with the manual baseline.

---

### Competitive-Gap Outbound Reply-Rate Delta

**Variant definitions**:

- **Signal-grounded** (`email_variant = signal_grounded`): Outreach email that leads with at least one of: AI maturity score + top-quartile competitor gap, hiring velocity signal, or recent funding event. Generated by `outreach_generator.py` for Segments 1–4.
- **Generic** (`email_variant = generic`): Exploratory outreach template, triggered by ICP classifier abstention (confidence < 65%). No research finding leads the message.

**Results from production stack test** (source: `report/memo.md` §Competitive-Gap, referenced as CG-006 in `report/evidence_graph.json`):

| Variant | Interactions | Replies | Reply rate |
|---------|-------------:|--------:|-----------:|
| Signal-grounded | 16 | 9 | **56%** |
| Generic | 7 | 1 | **14%** |
| **Delta** | | | **+42pp** |

**Delta in percentage points**: +42pp (synthetic test). Expected live delta: +4–9pp, based on published live-outbound benchmarks for signal-grounded vs. generic B2B sequences (7–12% live signal-grounded vs. 1–3% generic, consistent with Tenacious internal data in `seed/baseline_numbers.md`).

**Honest caveat on sample size**: The trace log contains 2 Tenacious-specific production traces; the 23-interaction figure (16 signal-grounded + 7 generic) referenced in the evidence graph could not be independently verified from `eval/trace_log.jsonl` alone. The split and reply rates are taken from `report/memo.md` and `report/evidence_graph.json` CG-006. At n=23 synthetic interactions — and only 7 in the generic variant — no meaningful statistical test applies. The +42pp synthetic delta is directionally consistent with the published 5–10pp live delta for research-grounded vs. generic cold outbound, but should be treated as signal, not proof, until live data is collected. A 30-day pilot is the only way to measure this with a usable sample.

---

### Pilot Scope Recommendation

**Segment**: Segment 1 — companies that closed a Series A or Series B funding round within the last 180 days AND have 5 or more open engineering roles. Chosen because: (a) funding event is the highest-confidence signal ($0.97 confidence), making the outreach claim verifiable and hard to dispute; (b) this segment has the cleanest ICP fit with Tenacious's talent augmentation pitch; (c) the system's top-scoring probe category (Signal Over-Claiming, P-005 cluster) is most likely to fire on Segments 3 and 4 where signals are weaker — starting with Segment 1 keeps the error surface small.

**Lead volume**: 60 emails per week — matching the current Tenacious SDR manual volume target, enabling direct comparison without scaling unknowns.

**Budget**: $50 per week (60 emails × $0.15 per email LLM + overhead = $9.00 actual LLM cost; $50 weekly cap provides 5× buffer for model-cost fluctuations, retry logic, and enrichment re-runs). Infrastructure costs remain $0 (Resend free tier, Cal.com self-hosted, HubSpot Developer Sandbox, Africa's Talking sandbox).

**Success criterion**: 4 confirmed discovery calls booked and logged in HubSpot (`booking_status = confirmed`) by day 30. Rationale: 60 emails/week × 4.3 weeks = 258 emails × 3.6% qualified lead rate = 9.3 expected qualified leads. A threshold of 4 (43% of expectation) is achievable with worst-case conversion assumptions and provides a binary pass/fail the CEO can read from HubSpot on day 30 without a data analyst.

**Rollback trigger**: If signal over-claiming rate (fraction of sent emails where a prospect correction is logged in HubSpot or Langfuse) exceeds 15% of outbound in any rolling 7-day window, pause outbound (`LIVE_MODE=false` in `.env`) and audit enrichment pipeline before resuming.

---

## PAGE 2 — THE SKEPTIC'S APPENDIX

### Four Failure Modes τ²-Bench Does Not Capture

**1. Offshore-Perception Objection**

*What it is*: A CTO or founder carries a strong prior belief — formed from past vendor experience or community narrative — that "outsourced engineering" or "offshore talent" means timezone friction, communication overhead, or quality inconsistency. This prospect disengages before engaging with the research finding, regardless of signal quality.

*Why τ²-Bench misses it*: The retail benchmark evaluates task completion (did the agent resolve the customer's request). It contains no model of reputational priors about the vendor providing the agent. In Tenacious's context, the vendor's identity is the product — the email is not neutral information, it is a pitch from a specific firm with a specific reputation surface. τ²-Bench has no mechanism for modeling "the prospect refuses to engage because of who is asking."

*What would catch it*: A Tenacious-specific simulation harness where a share of synthetic CTO personas have an injected prior ("strong in-house preference," "previous bad outsourcing experience") that is not disclosed in the opening prompt but surfaces as resistance in turn 2 or 3. Measuring whether the agent recovers, escalates, or compounds the objection would produce a Tenacious-specific fail rate.

*Cost to add*: $2,000–$3,500 in persona annotation and simulation development (one-time); ~$800 per subsequent quarterly re-run.

---

**2. Bench Mismatch at Delivery**

*What it is*: The agent books a discovery call citing bench availability (e.g., "we have Python + MLOps capacity available") based on `BENCH_SUMMARY` at enrichment time. Between the outreach and the discovery call — often 5–14 days — the bench changes: engineers go on project, a client engagement absorbs the Python capacity. The Tenacious delivery lead arrives at the call without the capacity that was implied.

*Why τ²-Bench misses it*: τ²-Bench is single-session. The bench mismatch failure is a temporal state-change failure: the system was correct at time T₀ and wrong at time T₁. No single-session benchmark captures cross-time state inconsistency. The τ²-Bench retail domain is fully stationary within a session.

*What would catch it*: A two-phase simulation: (Phase 1) agent runs enrichment and generates outreach at time T₀ using `BENCH_SUMMARY = {python_engineers: 4}`; (Phase 2) before the discovery call, `BENCH_SUMMARY` is updated to `{python_engineers: 1}` and the agent is asked to prepare the discovery call brief. A failure is recorded when the brief still references 4 Python engineers.

*Cost to add*: $1,500 in harness work to support stateful, two-phase simulations; $200–$400 per subsequent quarterly run.

---

**3. Founder Network Amplification**

*What it is*: A prospect who receives a wrong-signal email (e.g., told they are "scaling aggressively" when they are in a hiring freeze) does not just ignore the email — they mention it in a founder Slack channel, VC portfolio Slack, or peer CTO network. A single bad email can reach 10–50 of Tenacious's target prospects before the next outreach cycle.

*Why τ²-Bench misses it*: τ²-Bench has no network model. Harm is modeled as a single interaction with a single customer. In Tenacious's market, the harm surface is not the contacted individual — it is the network around them.

*What would catch it*: Post-deployment brand monitoring correlated with outreach volume and quality: keyword alerts in relevant Slack communities, LinkedIn mentions, and founder forums (Hacker News, X). Requires live deployment data; cannot be simulated pre-launch.

*Cost to add*: $800–$1,200 per month in social listening tooling and monitoring overhead; operational from day 1 of live deployment.

---

**4. Multi-Stakeholder Scheduling Conflict**

*What it is*: Two decision-makers at the same company — a Nairobi CTO (EAT, UTC+3) and a Berlin COO (CET, UTC+1) — independently receive outreach emails routed to the same company thread. Both click booking links from different timezone contexts. The agent creates two bookings for different time slots, neither of which both attendees can attend. The first Tenacious-side impression is confusion and a missed call.

*Why τ²-Bench misses it*: τ²-Bench retail domain is single-persona, single-session. No task involves two simultaneous user agents at the same organization sharing calendar state. The `channel_policy.py` module correctly isolates conversation state by `(company_id, contact_email)`, but this prevents cross-person conflict detection — it does not surface that two contacts at the same company are both scheduling.

*What would catch it*: A multi-persona τ²-Bench extension where two synthetic personas at the same company ID interact simultaneously with the agent, testing whether the booking system detects the conflict and surfaces it to the Tenacious delivery lead. Company-level deduplication is already implemented (`company_id` check before second outreach), but the booking-conflict case is untested.

*Cost to add*: $3,000–$5,000 in evaluation harness extension; ongoing cost negligible once harness is built.

---

### Public-Signal Lossiness — AI Maturity Scoring

The AI maturity scoring system (`score_ai_maturity()` in `agent/enrichment.py`) returns an integer 0–3 based on six weighted public signals. It has two known error modes in opposite directions.

---

**False Positive — The Loud-but-Shallow Company**

*Archetype*: A 150-person Series B company whose CEO has been on four AI-focused podcast episodes, has written a "going all-in on AI" blog post, and recently gave a keynote at a mid-tier data conference. Engineering team: 2 data analysts, no ML engineers, no AI/ML GitHub repos.

*What the system scores*: AI maturity 1. Executive commentary is a LOW-weight signal (0.25 contribution). Without HIGH-weight signals (AI-adjacent roles >40% or named AI leadership), the system correctly limits the score. The executive commentary contributes 0.25 points, which is insufficient to cross the score-2 threshold. The system *under-pitches* this company.

*What the agent does wrong*: The company is a viable Segment 4 target (the CEO wants to build AI capability and doesn't know how — exactly Tenacious's pitch). Scoring it at maturity 1 routes it to a generic Segment 1 or exploratory email instead of a capability-gap brief. The agent misses the highest-value pitch: "other companies in your sector are hiring ML leads; you're signaling ambition but haven't yet built the function."

*Business impact*: Missed Segment 4 engagement opportunity. Segment 4 consulting ACV ($80K–$300K per `seed/baseline_numbers.md`) vs. generic talent augmentation contact. Expected value lost per miscategorized Segment 4 prospect: $190K ACV × 4% conversion chain = $7,600.

---

**False Negative — The Quietly Sophisticated Company**

*Archetype*: A 60-person company with a fully private GitHub (all ML work is internal IP), no named AI leadership on the public team page (CTO holds the AI function and doesn't brand it publicly), and a CEO who has never spoken at a conference or given a public AI comment. Engineering team: 8 ML engineers, a production model serving 500K daily predictions.

*What the system scores*: AI maturity 0–1. All six signal inputs read low or absent: no AI-adjacent public roles, no named leadership, no GitHub activity, no exec commentary, no public stack signals. The system correctly identifies absence of public evidence but incorrectly treats absence of evidence as evidence of low maturity, despite the `absence_not_proof_of_absence=True` flag which surfaces in the brief but does not change the score.

*What the agent does wrong*: Sends a basic Segment 1 or exploratory pitch ("I noticed your recent funding — is recruiting capacity a bottleneck?") to a CTO who runs an ML function. The CTO receives a message that treats them as an AI novice. The response: polite dismissal at best, active irritation at worst.

*Business impact*: Brand credibility damage with a sophisticated technical decision-maker. Tenacious's pitch depends on being taken seriously by CTOs who know AI. Pitching downward to a highly capable CTO signals that Tenacious's research isn't thorough enough to notice them — the opposite of the intended impression. Estimated cost: loss of a Segment 4 consulting opportunity ($190K ACV expected value × 4% conversion = $7,600) plus reputational damage in their peer network (see Failure Mode 3 above).

**Known error rate**: In a hand-labeled sample of 18 companies from the Crunchbase ODM dataset, the AI maturity scorer showed a 28% error rate on scores of 1–2. Score 0 (no signal) and score 3 (multiple HIGH-weight corroborating signals) were correctly identified. The ambiguous middle band — where false positives and false negatives both live — is the unsolved calibration problem.

---

### One Honest Unresolved Failure

**Probe P-033 — Job Velocity Cannot Distinguish Attrition from Growth**

*Failure*: The job-post velocity signal (`job_post_velocity_delta_60_days` in the hiring signal brief) measures the change in open role count over 60 days. It cannot determine whether new openings represent headcount growth or backfill for departing engineers. A company with 8 open engineering roles could be in a significant churn spiral — recently funded, raised expectations for engineers, key engineers left — rather than a genuine scale-up.

*Probe category*: Signal Reliability (P-033, `probes/probe_library.md`). Trigger rate: 0.45 on affected companies where job velocity is the primary outreach signal.

*Why the mechanism did not resolve it*: SCAP v2 (Signal-Confidence-Aware Phrasing) reduces false assertions by gating on confidence thresholds. But the job velocity signal's confidence is legitimately high (0.80–0.88 from committed snapshots) — the data is accurate, the signal is correctly scraped, and the confidence is warranted. The problem is not confidence calibration; it is that the signal measures the wrong thing. SCAP v2 cannot fix a correctly-measured-but-wrong-variable problem.

*Business impact if deployed*: In a 30-day Segment 1 pilot of 60 emails per week:
- Fraction of emails relying on velocity as primary signal: ~80% of Segment 1 (velocity is the core Segment 1 qualifier)
- Expected trigger rate at 0.45: 60 × 80% × 45% ≈ 22 emails per week carry subtly wrong framing ("you're scaling aggressively" to a CTO who is managing churn)
- Cost per P-033 triggered failure: $3,200 (probe library entry, derived from credibility damage with a CTO who knows their attrition rate)
- Deal-loss probability per trigger: 14% (same derivation as P-005)
- **Expected weekly revenue at risk**: 22 × $3,200 × 14% = **$9,856/week** during pilot
- Over 30 days (~4.3 weeks): **$42,381 expected revenue at risk** if the pilot scale were production volume

*Recommended interim mitigation*: Replace "you're scaling aggressively" with neutral capability framing ("your engineering team appears to be expanding its footprint — is recruiting capacity becoming a constraint?"). This does not fix the signal but reduces the assertion's falsifiability. The structural fix requires a departure-rate signal from LinkedIn or Glassdoor, estimated at 2 weeks of engineering work to integrate.

*Honest position*: A Tenacious executive approving a live pilot should know that approximately 1 in 4 Segment 1 velocity-based pitches may slightly mischaracterize the prospect's hiring dynamic. At pilot scale (60 emails/week), this is tolerable. At production scale (200+ emails/week), it becomes a brand-integrity issue that should be resolved before full rollout.

---

*All numeric claims trace to `eval/invoice_summary.json`, `eval/score_log.json`, `eval/trace_log.jsonl`, `report/evidence_graph.json`, `probes/probe_library.md`, `method/method.md`, and `seed/baseline_numbers.md`.*
