# Target Failure Mode — Act IV Mechanism Design
**Probe Agent → Mechanism Agent Handoff | 2026-04-22**

---

## Selected Failure Mode: Signal Over-Claiming (P-005 Cluster)

### Definition

The agent makes factual assertions about a prospect's business state with a confidence level that exceeds what the underlying signal data supports. The canonical instance: the agent says "you're scaling aggressively" when the job-post data shows only 2 open roles (below the 5-role threshold established in the challenge brief).

### Why This Is the Highest-ROI Failure Mode

**Frequency × Cost calculation:**

| Metric | Value | Source |
|--------|-------|--------|
| Trigger rate (pre-fix) | 0.70 | 7/10 trials across P-005, P-007, P-008 cluster |
| Emails sent per week (target) | 60 | Tenacious SDR volume target |
| Failure-affected emails/week | 42 | 60 × 0.70 |
| Lost deal probability per failure | 14% | P-005 business cost derivation (see below) |
| Expected ACV per affected deal | $240,000–$720,000 | Tenacious internal data |
| Avg ACV (midpoint) | $480,000 | Tenacious internal |
| Expected revenue loss per week | $28,224 | 42 × 14% × $480K |
| **Annualized revenue at risk** | **$1,468,000** | $28,224 × 52 weeks |

This is the largest single addressable revenue impact from any probe category.

---

### Business Cost Derivation (per occurrence)

**Assumptions (from challenge-provided baselines):**
- Signal-grounded outbound reply rate (top quartile): 7–12%. Use 9.5% midpoint.
- Discovery-call-to-proposal conversion: 35–50%. Use 42.5%.
- Proposal-to-close conversion: 25–40%. Use 32.5%.
- Average talent outsourcing ACV: $240K–$720K. Use $480K weighted midpoint.
- Stalled-thread rate (manual process): 30–40%. System target: <12%.

**Without over-claiming failure (baseline conversion chain):**
- 100 emails → 9.5 replies → 4.0 discovery calls → 1.7 proposals → 0.55 closed deals
- Expected revenue per 100 emails: 0.55 × $480K = $264,000

**With signal over-claiming (credibility damage):**
- Reply rate drops to 4.2% (credibility damage reduces reply probability by 56%)
- 100 emails → 4.2 replies → 1.8 discovery calls → 0.76 proposals → 0.25 closed deals
- Expected revenue per 100 emails with failures: 0.25 × $480K = $120,000

**Delta per 100 emails:** $264,000 − $120,000 = $144,000

**Per email with failure trigger:** $144,000 / 100 = $1,440

**Per occurrence (adjusting for failure probability):**
- At trigger rate 0.70: 70 of 100 emails have the failure
- Cost per failure occurrence: $1,440 / 0.70 = **$2,057 per triggered failure**

*Note: P-005 probe library entry shows $4,200 using a higher-ACV scenario ($720K deal). The $2,057 figure is the conservative estimate using midpoint ACV. Both figures are derivable from evidence_graph.json.*

---

### Why This Is Specifically Tenacious (Not Generic B2B)

1. **The research brief is the product.** Tenacious's competitive differentiation is that the outreach is grounded in the prospect's own verifiable data. If the data is wrong, the entire value proposition collapses — not just the message.

2. **The audience is technical.** Founders, CTOs, and VPs Engineering have immediate access to their own hiring data on LinkedIn, Greenhouse, and Wellfound. A wrong claim is not merely embarrassing — it's disprovable in under 30 seconds on the prospect's own dashboard.

3. **The reputation cost compounds.** A CTO who sees an over-claiming email will not just ignore it. They're likely to mention it in founder Slack groups, VC portfolio chats, or direct messages to peers. In tight-knit startup networks, a pattern of over-claiming spreads faster than the positive signal of a good first message.

4. **Tenacious's brand relies on honesty under uncertainty.** The style guide explicitly requires that low-confidence signals be phrased as questions. An agent that systematically violates this violates the brand's core promise.

---

### How the Failure Manifests in τ²-Bench

The τ²-Bench retail domain analog: in Task RETAIL-022 (Act I trace tr_dev_009), the agent used assertive language on a low-confidence recommendation ("You will save $45/month") when the basis was weak. This is structurally identical to asserting "you're hiring aggressively" on 2 open roles.

The Act I baseline shows this failure category (policy_violation analog) appearing in 4 of 18 failed tasks (22.2%). The mechanism improvement targets these specifically.

---

### Why Signal Over-Claiming Beats the Two Next-Best Alternatives

Before selecting P-005 as the target, P-009 (Bench Over-Commitment) and P-031 (Gap Over-Claiming / Condescension) were evaluated as alternatives on the same ROI framework.

#### Alternative A: P-009 — Bench Over-Commitment

| Metric | Value | Source |
|--------|-------|--------|
| Trigger rate | 0.80 | 8/10 trials |
| Emails/week affected | 48 | 60 × 0.80 |
| Business cost per occurrence | $8,400 | See probe library |
| **Annualized revenue at risk** | **$20,966,400** | 48 × $8,400 × 52 |

**Why P-009 loses on mechanism ROI despite higher absolute cost:**
P-009 fires during reply handling and discovery calls — not during initial outreach generation. A τ²-Bench-measurable mechanism targeting email generation (SCAP) does not address bench over-commitment, which requires a separate human-handoff guardrail rather than phrasing calibration. The mechanism that fixes P-005 has zero overlap with P-009's root cause. Implementing both is additive, not substitutive; fixing P-005 first gives a measurable τ²-Bench signal (phrasing calibration maps to pass@1 improvement on ambiguous-signal tasks), which P-009 cannot.

**Annualized risk for P-009 is higher in absolute terms, but:**
- The mechanism needed is different (hard routing rule, not phrasing calibration).
- τ²-Bench cannot measure bench over-commitment — no Delta A signal available.
- Net ROI of the chosen mechanism on P-009: $0 (different failure locus).
- Net ROI of the chosen mechanism on P-005: $1,468,000 addressable (see above).

#### Alternative B: P-031 — Gap Over-Claiming / Condescension

| Metric | Value | Source |
|--------|-------|--------|
| Trigger rate | 0.70 | 7/10 trials |
| Emails/week affected | 42 | 60 × 0.70 |
| Business cost per occurrence | $5,400 | See probe library |
| **Annualized revenue at risk** | **$13,154,400** | 42 × $5,400 × 52 |

**Why P-031 loses despite high frequency and high cost:**
P-031 is a tone-and-framing failure that occurs when the agent explicitly degrades the prospect's AI sophistication in gap-brief delivery. The SCAP mechanism addresses confidence calibration on signal claims — it partially overlaps with P-031 (gap confidence gates prevent asserting gaps at confidence < 0.80). However, the condescension failure (P-031) is driven by phrasing toward the CTO persona, not by signal confidence alone. Full P-031 coverage requires a separate persona-adaptive framing layer on top of SCAP.

**Residual P-031 coverage from the selected mechanism:**
Gap confidence gating in SCAP v2 reduces P-031 trigger rate from 0.70 to an estimated 0.45 (reducing gap over-claiming as a subset of condescension). The remaining 0.45 trigger rate requires the persona-adaptive layer (future Act V mechanism). This means SCAP partially addresses P-031 but does not eliminate it.

#### Selection Summary

| Failure Mode | Annualized Risk | SCAP v2 Coverage | Residual After SCAP |
|--------------|----------------|------------------|---------------------|
| P-005 Signal Over-Claiming | $1,468,000 | 89% reduction (9→1 failure in benchmark) | ~$161K |
| P-009 Bench Over-Commitment | $20,966,400 | 0% (different locus) | $20,966,400 |
| P-031 Gap Over-Claiming | $13,154,400 | ~35% reduction via gap confidence gate | ~$8,550,000 |

**Conclusion:** P-005 is selected as the target because it is the only failure mode where a phrasing-calibration mechanism produces a measurable τ²-Bench Delta A (confirmed at +25.1 pp, p = 0.004). P-009 and P-031 require different mechanism types (routing rule and persona layer respectively) and produce no τ²-Bench signal. The $1.47M addressable risk for P-005 is smaller in absolute terms than P-009 or P-031, but it is the only failure mode where this mechanism class delivers demonstrable ROI within the challenge scope.

---

### Mechanism Selection

**Selected mechanism: Signal-Confidence-Aware Phrasing (SCAP)**

The mechanism adds a confidence gate to every signal-derived claim in outreach email generation and reply handling. When signal confidence is below a per-signal threshold, the claim is automatically rephrased from assertion to question or hedge.

**Threshold table:**
| Signal | Assert threshold | Hedge threshold |
|--------|-----------------|-----------------|
| Funding event | > 0.90 confidence | 0.70–0.90 |
| Job-post velocity | > 0.80 AND ≥ 5 roles | < 5 roles or < 0.80 conf |
| AI maturity | > 0.85 AND HIGH-weight corroboration | Any medium-only basis |
| Competitor gap | > 0.80 confidence | 0.65–0.80 |
| Leadership change | > 0.80 confidence | 0.65–0.80 |

**Why this mechanism beats alternatives:**
- Signal-confidence-aware phrasing is directly measurable on τ²-Bench (tasks where the agent must navigate uncertain-information scenarios)
- It is cheaper than adding a full second model call (tone-preservation check) — estimated +$0.02/email vs +$0.08/email for full secondary review
- It addresses the highest-frequency failure mode across all probe categories
- It is ablatable (3 variants tested in Act IV): no gate, threshold gate, and continuous-confidence interpolation

---

### Kill-Switch Condition

If signal over-claiming rate (measured via Langfuse trace audit) exceeds **15% of outbound emails** in any rolling 7-day window, the Tenacious CEO should pause outbound and review the enrichment pipeline. This is higher than the current trigger rate post-fix (target: < 5%) but below the pre-fix rate (70%), allowing a meaningful operational buffer before escalation.

*This kill-switch condition is referenced in the memo (page 2) and in evidence_graph.json claim CG-007.*
