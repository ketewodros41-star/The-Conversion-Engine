# Tenacious Conversion Engine
**Automated Lead Generation and Conversion System**
*10 Academy Challenge Week 10 | Tenacious Consulting and Outsourcing*

---

## Inheritor Docs

- `SETUP.md` - explicit prerequisites, verified versions, config variables, and run order
- `DIRECTORY_INDEX.md` - top-level folder map for the whole repository
- `HANDOFF_NOTES.md` - known limitations and next steps a successor will hit

---

## ⚠️ IMPORTANT: Kill Switch

**`LIVE_MODE` defaults to `false`.** All outbound email and SMS routes to the staff sink unless you explicitly set `LIVE_MODE=true` in your `.env` file. Do NOT set `LIVE_MODE=true` without Tenacious executive team approval.

```bash
# .env (default — safe)
LIVE_MODE=false
STAFF_SINK_EMAIL=sink@tenacious-challenge.example.com
STAFF_SINK_NUMBER=+254700000000
```

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                   TENACIOUS CONVERSION ENGINE                     │
│                                                                  │
│  ┌─────────────┐    ┌───────────────┐    ┌──────────────┐       │
│  │  Enrichment  │    │  ICP Classifier│    │  Outreach    │       │
│  │  Pipeline    │───▶│  w/ Abstention │───▶│  Generator   │       │
│  │             │    │               │    │  (SCAP v2)   │       │
│  │ Crunchbase  │    │ Seg 1,2,3,4   │    └──────┬───────┘       │
│  │ Job Posts   │    │ Confidence    │           │               │
│  │ Layoffs.fyi │    │ Thresholds    │           │ prompt        │
│  │ Leadership  │    └───────────────┘           ▼               │
│  │ AI Maturity │                       ┌──────────────────┐     │
│  └─────────────┘                       │  Backbone LLM    │     │
│                                        │  OpenRouter      │     │
│                                        │  (gpt-4o-mini /  │     │
│                                        │   Claude Sonnet) │     │
│                                        └──────┬───────────┘     │
│                                               │ email text       │
│                                               ▼                  │
│  ┌─────────────┐    ┌───────────────┐   ┌──────────────┐       │
│  │  HubSpot    │◀───│  CRM Agent   │◀──│  Email/SMS   │       │
│  │  CRM (MCP)  │    │              │   │  Handlers    │       │
│  └─────────────┘    │  Audit Trail  │   │  (Resend /   │       │
│                     └───────────────┘   │  Africa's    │       │
│  ┌─────────────┐                        │  Talking)    │       │
│  │  Cal.com    │◀───────────────────────└──────┬───────┘       │
│  │  Calendar   │          Reply handling        │               │
│  │  (Docker)   │          ├─ Qualify            │               │
│  └─────────────┘          ├─ Schedule           │               │
│                            └─ Unsubscribe        │               │
│  ┌─────────────┐                                                 │
│  │  Langfuse   │◀── Per-trace cost attribution                  │
│  │  (Cloud)    │    OpenTelemetry                               │
│  └─────────────┘                                                 │
└──────────────────────────────────────────────────────────────────┘
```

**Channel hierarchy** (enforced in code):
1. **Email** (primary) — cold outreach, signal-grounded
2. **SMS** (secondary) — warm leads only, scheduling only, explicit consent required
3. **Voice** (bonus tier) — discovery call, human Tenacious delivery lead

---

## Repository Structure

```
/planning/
  execution_plan.md         — Dependency DAG, milestones, agent assignments

/eval/
  score_log.json            — τ²-Bench pass@1 scores, baselines, Delta A
  trace_log.jsonl           — Full τ²-Bench trajectories + production traces
  baseline.md               — Act I baseline report (max 400 words)
  latency_metrics.json      — p50/p95 latency for email and SMS channels
  harness.py                — τ²-Bench evaluation wrapper
  tau2_runner.py            — Benchmark runner with Langfuse integration

/agent/
  main.py                   — FastAPI orchestrator, webhook handlers
  enrichment.py             — Signal enrichment pipeline (Crunchbase + jobs + layoffs)
  icp_classifier.py         — ICP segment classifier with abstention
  outreach_generator.py     — Signal-grounded email generator (SCAP v2)
  email_handler.py          — Resend integration (primary channel)
  sms_handler.py            — Africa's Talking integration (secondary channel)
  hubspot_crm.py            — HubSpot client (MCP primary, REST fallback)
  calcom_booking.py         — Cal.com calendar booking
  requirements.txt          — Python dependencies
  hiring_signal_brief.json  — Example enriched brief (NexusAI Labs synthetic)
  hiring_signal_brief.schema.json — JSON schema for hiring-signal brief
  competitor_gap_brief.json — Example competitor gap analysis
  competitor_gap_brief.schema.json — JSON schema for competitor-gap brief

/probes/
  probe_library.md          — 35 structured adversarial probes
  failure_taxonomy.md       — Category analysis with trigger rates + business costs
  target_failure_mode.md    — Highest-ROI failure mode + mechanism selection rationale

/method/
  method.md                 — SCAP v2 mechanism design, hyperparameters, ablations
  ablation_results.json     — pass@1, CI, cost for all 4 variants + GEPA baseline
  held_out_traces.jsonl     — Archived trace artifact from an earlier evaluation pass

/report/
  memo.md                   — 2-page executive memo (memo.pdf equivalent)
  evidence_graph.json       — Machine-readable claim → source mapping (21 claims)

/market/
  market_space.csv          — (distinguished tier) Sector × size × AI-maturity map
  top_cells.md              — Top 3-5 outbound priority cells
  methodology.md            — Scoring validation, precision/recall

/qa/
  final_validation_report.md — Submission readiness check

README.md                   — This file
```

---

## Quick Start

### Prerequisites
- Python 3.11+
- Docker (for Cal.com)
- Accounts: Resend (free), Africa's Talking (sandbox), HubSpot Developer Sandbox, Langfuse (free cloud)

### Setup

```bash
# Clone and install
git clone <repo-url>
cd tenacious-conversion-engine
pip install -r agent/requirements.txt

# Install Playwright browsers
playwright install chromium

# Copy and configure environment
cp .env.example .env
# Edit .env with your API keys (see below)

# Start Cal.com locally
docker compose up -d calcom

# Run Playwright installation check
python -c "from playwright.sync_api import sync_playwright; print('Playwright OK')"
```

### Required Environment Variables

```bash
# === KILL SWITCH (default: off) ===
LIVE_MODE=false                           # NEVER set true without Tenacious approval

# === LLM ===
ANTHROPIC_API_KEY=sk-ant-...              # Claude Sonnet 4.6 for eval tier
OPENROUTER_API_KEY=sk-or-...             # Optional: dev tier (Qwen3/DeepSeek)

# === EMAIL (primary channel) ===
RESEND_API_KEY=re_...                     # Resend free tier
SENDER_EMAIL=outreach@your-domain.com
STAFF_SINK_EMAIL=sink@your-test.com      # Required: receives all outbound in sandbox

# === SMS (secondary channel) ===
AT_USERNAME=sandbox
AT_API_KEY=...                            # Africa's Talking sandbox API key
STAFF_SINK_NUMBER=+254700000000          # Required: receives all SMS in sandbox

# === CRM ===
HUBSPOT_ACCESS_TOKEN=pat-na1-...         # HubSpot Developer Sandbox private app
HUBSPOT_TRANSPORT=mcp                    # Preferred: MCP transport, falls back to REST if unavailable
HUBSPOT_MCP_URL=http://localhost:8080/mcp # Optional MCP gateway endpoint

# === CALENDAR ===
CALCOM_URL=http://localhost:3000
CALCOM_API_KEY=...                        # Cal.com admin API key
CALCOM_EVENT_TYPE_ID=1                   # Discovery call event type ID

# === OBSERVABILITY ===
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com
```

### Hiring Velocity Snapshot Store

- Public hiring velocity is computed from persisted snapshots, not inferred backfill.
- Committed examples live in `data/public_signal_catalog.json` and `data/job_post_snapshots.json`.
- For an unknown company, the first scrape records a point-in-time snapshot. The 60-day delta is emitted only after a second persisted snapshot exists.

### Brief Contract Notes

- `agent/hiring_signal_brief.schema.json` requires each committed signal to carry `observed_at`, `source_attribution`, `confidence`, and `confidence_tier`.
- AI maturity scoring now treats `ai_leadership` as a distinct high-weight input separate from `leadership_change`, so a named Head of AI or VP Data can be captured even when there was no recent leadership transition.

### Run the API Server

```bash
uvicorn agent.main:app --reload --port 8000
```

### Process a Synthetic Prospect

```bash
curl -X POST http://localhost:8000/api/process-prospect \
  -H "Content-Type: application/json" \
  -d '{
    "crunchbase_id": "cb_nexusai_2024",
    "company_name": "NexusAI Labs",
    "contact_email": "synthetic-alex@nexusai-labs.example.com",
    "contact_name": "Alex Rivera",
    "contact_title": "CTO",
    "is_synthetic": true
  }'
```

### Run τ²-Bench Baseline

```bash
cd eval/
python tau2_runner.py \
  --model claude-sonnet-4-6 \
  --temperature 0.0 \
  --mechanism none \
  --slice dev \
  --trials 5 \
  --output trace_log.jsonl
```

### Run SCAP v2 Mechanism (current documented evaluation path)

```bash
cd eval/
python tau2_runner.py \
  --model claude-sonnet-4-6 \
  --temperature 0.0 \
  --mechanism scap_v2 \
  --slice dev \
  --trials 1 \
  --output trace_log.jsonl
```

### Validate Evidence Graph

```bash
python report/validate_evidence_graph.py report/evidence_graph.json
```

---

## Key Design Decisions

### 1. Email-First Channel Architecture
Unlike voice-first compliance automation, Tenacious prospects (founders, CTOs, VPs Engineering) live in email. Cold SMS to this segment is intrusive; cold voice is rare. Channel hierarchy is enforced in code: SMS activation requires explicit email reply AND phone number provided AND scheduling intent confirmed.

### 2. ICP Classifier with Abstention
Rather than forcing every prospect into one of four segments, the classifier abstains when confidence is below 65%, sending an exploratory email instead. This prevents the highest-cost failure mode: a Segment 2 (restructuring) pitch to a founder who just closed a Series B.

### 3. Signal-Confidence-Aware Phrasing (SCAP v2)
Every signal-derived claim in outreach emails is tagged with its source signal and confidence score. A three-tier gate (assert / hedge / question) determines phrasing based on signal-specific thresholds. This reduces signal over-claiming from 70% trigger rate to under 10%, adding only $0.13/email in cost.

### 4. Bench-Gated Commitment Policy
The agent never commits to specific headcount or timelines. Any staffing or timeline question routes to the delivery lead. This prevents the second-highest-cost failure mode (bench over-commitment).

### 5. Multi-Thread Isolation
Conversation state is keyed by `(company_id, contact_email)` — never shared across contacts, even at the same company. Company-level deduplication check before second outreach.

---

## Data Handling

- All prospects during the challenge week are **synthetic** — derived from Crunchbase ODM firmographics + fictitious contact details
- All outbound routes to staff sink by default (`LIVE_MODE=false`)
- All branded content marked `"is_draft": true` in metadata
- Seed materials (sales deck, pricing, case studies) will be deleted from personal infrastructure at end of challenge week
- Code may be retained in program repo

---

## Reproducing Results

All results in the final memo and evidence_graph.json are reproducible:

1. **Baseline** (CG-002): `python eval/tau2_runner.py --mechanism none --slice dev`
2. **SCAP v2** (CG-001): `python eval/tau2_runner.py --mechanism scap_v2 --slice dev`
3. **Delta A** (CG-003): read `eval/score_log.json` delta_analysis for the current documented comparison
4. **Evidence graph** (all claims): `python report/validate_evidence_graph.py report/evidence_graph.json`

---

## Cost Summary

| Component | Actual | Budget | Status |
|-----------|--------|--------|--------|
| Africa's Talking SMS | $0 | $0 | ✅ |
| HubSpot Developer Sandbox | $0 | $0 | ✅ |
| Cal.com self-hosted | $0 | $0 | ✅ |
| Langfuse cloud | $0 | $0 | ✅ |
| LLM dev tier | $3.15 | ≤$4 | ✅ |
| LLM eval tier | $6.35 | ≤$12 | ✅ |
| **Total** | **$9.50** | **≤$20** | **✅** |

---

## License and Attribution

- Crunchbase ODM sample: Apache 2.0 (github.com/luminati-io/Crunchbase-dataset-samples)
- layoffs.fyi data: CC-BY
- τ²-Bench: Apache 2.0 (github.com/sierra-research/tau2-bench)
- Tenacious seed materials: Limited license for challenge week only — do not redistribute

---

*Built for 10 Academy Challenge Week 10 | Lead author: kidus@10academy.org*
