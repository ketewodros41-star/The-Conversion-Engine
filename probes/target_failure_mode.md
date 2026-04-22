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
