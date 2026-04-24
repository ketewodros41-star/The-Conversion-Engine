# Setup Instructions

This document is the inheritor-focused bootstrap guide for local setup.

## Verified Environment

- Windows 11 or macOS/Linux with Python `3.11.9`
- `pip 24.0`
- Node.js `20.11.1` and npm `10.2.4` for Playwright browser install
- Docker Desktop `4.31+` for local Cal.com

## Verified Dependency Versions

These are the versions this repo is documented against for local bring-up:

- `anthropic==0.40.0`
- `httpx==0.27.0`
- `resend==2.0.0`
- `africastalking==1.2.0`
- `aiohttp==3.9.0`
- `playwright==1.44.0`
- `pandas==2.2.0`
- `numpy==1.26.0`
- `scipy==1.13.0`
- `langfuse==2.30.0`
- `opentelemetry-sdk==1.24.0`
- `fastapi==0.111.0`
- `uvicorn==0.29.0`
- `pydantic==2.7.0`
- `python-dotenv==1.0.0`
- `structlog==24.2.0`

## Required Configuration

Copy `.env.example` to `.env` and set:

- `LIVE_MODE`: Safety kill switch. Keep `false` unless explicitly authorized.
- `STAFF_SINK_EMAIL`: Where all outbound email is routed in sandbox mode.
- `STAFF_SINK_NUMBER`: Where all outbound SMS is routed in sandbox mode.
- `ANTHROPIC_API_KEY`: Required for outbound email generation.
- `OPENROUTER_API_KEY`: Optional dev-tier model key.
- `RESEND_API_KEY`: Required for outbound email and replies.
- `SENDER_EMAIL`: Verified sender identity for Resend.
- `AT_USERNAME`, `AT_API_KEY`, `AT_SENDER_ID`: Africa's Talking credentials.
- `HUBSPOT_ACCESS_TOKEN`: HubSpot private app token.
- `HUBSPOT_TRANSPORT`: Preferred transport mode. Use `mcp` for MCP-backed writes; source falls back to REST if MCP is unavailable.
- `HUBSPOT_MCP_URL`: MCP bridge endpoint when `HUBSPOT_TRANSPORT=mcp`.
- `CALCOM_URL`, `CALCOM_API_KEY`, `CALCOM_EVENT_TYPE_ID`: Calendar connection and booking target.
- `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST`: Observability and eval tracing credentials.

## Local Run Order

1. Create a Python 3.11 virtual environment.
2. Install Python dependencies from `agent/requirements.txt`.
3. Install Playwright Chromium with `playwright install chromium`.
4. Copy `.env.example` to `.env` and fill in credentials.
5. Start Cal.com or point `CALCOM_URL` at an existing environment.
6. Start the API with `uvicorn agent.main:app --reload --port 8000`.
7. Verify `GET /health`.
8. Send a synthetic prospect to `POST /api/process-prospect`.
9. Register webhook endpoints only after the API is reachable from the relevant providers.

## Smoke Checks

- `python -c "from playwright.sync_api import sync_playwright; print('Playwright OK')"`
- `uvicorn agent.main:app --reload --port 8000`
- `curl http://localhost:8000/health`
- `python report/validate_evidence_graph.py report/evidence_graph.json`

## Bootstrapping Notes

- The repo assumes sandbox-safe outbound by default through sink email and sink SMS.
- Current HubSpot integration in `agent/hubspot_crm.py` supports MCP as the primary path and falls back to direct REST if the MCP bridge is unavailable.
- Cal.com booking fallback data is returned when the live API is unavailable so static demos do not hard fail.
- Job-post velocity is emitted only from real persisted public-page snapshots. Committed examples live in `data/public_signal_catalog.json` and `data/job_post_snapshots.json`; unknown companies get a point-in-time open-role signal until a second snapshot exists 60 days later.
