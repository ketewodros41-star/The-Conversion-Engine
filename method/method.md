# Act IV Mechanism - Signal-Confidence-Aware Phrasing (SCAP v2)
**Mechanism Agent | 2026-04-24**

---

## 1. Target Failure and Design Rationale

Target failure mode: `P-005` from `probes/target_failure_mode.md`.

Root cause: the agent treated weak signals as if they were strong signals. In practice that meant a low-evidence hiring or gap signal was still phrased as a fact. The business problem is not just wrong content; it is over-assertion under uncertainty.

Why SCAP addresses the root cause: SCAP does not try to guess better facts after generation. It changes how every signal is phrased before the LLM writes the email by injecting signal-specific instructions derived from the confidence attached to each input signal.

---

## 2. Re-Implementable Mechanism Spec

Inputs required per prospect:

- A structured `hiring_signal_brief` with signal objects carrying `confidence`, `confidence_tier`, and `brief_language`.
- A competitor-gap brief with per-gap confidence and evidence fields.
- A base outreach prompt.

Algorithm:

1. Read the structured signals for funding, job velocity, layoffs, AI maturity, and competitor gaps.
2. For each signal, compare `confidence` to the signal-specific assert and hedge thresholds.
3. Emit one phrasing instruction per signal:
   - `ASSERT` when confidence is above the assert threshold.
   - `HEDGE` when confidence is between hedge and assert.
   - `QUESTION` when confidence is below hedge.
4. Append those instructions to the system prompt before generation.
5. Forbid layoff-led openers regardless of confidence.
6. Forbid explicit headcount or delivery commitments regardless of confidence.
7. Generate the email with deterministic temperature.

Reference prompt-construction pseudocode:

```python
ASSERT_THRESHOLDS = {
    "funding_event": 0.90,
    "job_post_velocity": 0.80,
    "ai_maturity": 0.85,
    "competitor_gap": 0.80,
}

HEDGE_THRESHOLDS = {
    "funding_event": 0.75,
    "job_post_velocity": 0.65,
    "ai_maturity": 0.70,
    "competitor_gap": 0.65,
}

def build_scap_instructions(signals: dict) -> list[str]:
    instructions = []
    for signal_name, signal in signals.items():
        confidence = signal.get("confidence", 0.0)
        if confidence >= ASSERT_THRESHOLDS.get(signal_name, 0.90):
            mode = "ASSERT"
        elif confidence >= HEDGE_THRESHOLDS.get(signal_name, 0.70):
            mode = "HEDGE"
        else:
            mode = "QUESTION"
        instructions.append(f"{signal_name}: {mode}")
    instructions.append("layoff_event: never use as cold-open")
    instructions.append("bench_commitment: never promise headcount or start date")
    return instructions
```

Operational effect:

- High-confidence funding can be stated directly.
- Medium-confidence hiring velocity must be hedged.
- Low-confidence competitor gaps must be framed as questions.

---

## 3. Hyperparameters

| Parameter | Value |
|-----------|------:|
| Funding assert threshold | 0.90 |
| Funding hedge threshold | 0.75 |
| Job velocity assert threshold | 0.80 |
| Job velocity hedge threshold | 0.65 |
| Job velocity minimum role count | 5 |
| AI maturity assert threshold | 0.85 |
| AI maturity hedge threshold | 0.70 |
| Competitor-gap assert threshold | 0.80 |
| Competitor-gap hedge threshold | 0.65 |
| Max email word count | 180 |
| Model pin for current eval logs | `openrouter/openai/gpt-4o-mini` |
| Temperature | `0.0` |

Business rules layered on top:

- Never open cold outreach with a layoff event.
- Never promise exact staffing capacity or start date.
- Never name a competitor directly in the email body.

---

## 4. Ablation Variants

### Variant A - Baseline

No confidence-aware phrasing. Signals are usable as normal prompt facts.

What this tests: whether SCAP adds anything over the unmodified prompt.

### Variant B - Binary Gate

Signals are either asserted or converted into questions. No hedge tier.

What changed from the main method: the middle `HEDGE` band is removed.

What this tests: whether a three-tier system is materially better than a simpler assert/question split.

### Variant C - Continuous Interpolation

Phrasing strength is selected from multiple confidence buckets rather than the chosen three-tier design.

What changed from the main method: discrete `ASSERT/HEDGE/QUESTION` is replaced by a more granular interpolation scheme.

What this tests: whether extra granularity improves outcomes or just adds tuning complexity.

### Variant D - SCAP v2 (Selected)

Three-tier phrasing with signal-specific thresholds and hard business-rule overrides.

What this tests: the full production mechanism.

---

## 5. Current Evidence State

The current committed evidence is in `eval/score_log.json` and `method/ablation_results.json`.

What the repo can support honestly today:

- There are multiple baseline and SCAP runs on the dev slice.
- `ablation_results.json` documents the intended variant comparison.
- `score_log.json` contains the currently committed comparison numbers.

What the repo does not claim anymore:

- A sealed held-out statistical win not cleanly supported by the current committed logs.

This keeps the design record honest while preserving the mechanism description and test plan.

---

## 6. Statistical Test Plan

Primary test: one-sided two-proportion z-test comparing pass@1 of Variant D against Variant A on the same slice, same model family, and same trial budget.

Comparison definition:

- Null hypothesis: SCAP v2 does not improve pass@1 over baseline.
- Alternative hypothesis: SCAP v2 improves pass@1 over baseline.

Decision rule:

- Report the observed delta in percentage points.
- Report the 95% confidence interval on the delta.
- Treat `p < 0.05` as statistically significant.

Secondary analysis:

- Compare Variant D against the automated-optimization baseline directionally.
- Treat that comparison as exploratory unless the same-slice, same-model sample size is large enough.

---

## 7. Reproduction Notes

Current documented eval path:

```bash
cd eval/
python tau2_runner.py \
  --model openrouter/openai/gpt-4o-mini \
  --temperature 0.0 \
  --mechanism scap_v2 \
  --slice dev \
  --trials 1 \
  --output trace_log.jsonl
```

Artifacts to inspect after running:

- `eval/score_log.json`
- `eval/trace_log.jsonl`
- `method/ablation_results.json`

---

## 8. Why This Mechanism Was Chosen

`P-009` is costlier than `P-005`, but it is a policy and handoff problem, not a phrasing problem. SCAP v2 was selected because it directly attacks the highest-ROI failure mode that can be reduced by a prompt-time mechanism without pretending to solve inventory or staffing-control failures that belong elsewhere in the system.
