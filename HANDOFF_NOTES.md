# Handoff Notes

## Known Limitations

- `agent/hubspot_crm.py` now prefers MCP transport and falls back to direct REST if the MCP bridge is unavailable. If you need hard-fail MCP-only behavior, remove the REST fallback before go-live.
- `agent/enrichment.py` now has public-page scraping paths for Wellfound, BuiltIn, and LinkedIn public jobs, but selectors are brittle and should be regression-tested whenever those sites change DOM structure.
- Cal.com booking link generation is centralized, but the current generated path is a simple static link pattern. Replace it with the exact public booking URL for your Cal.com event type before go-live.
- Langfuse and OpenTelemetry are declared dependencies, but production observability wiring is still lighter than the architecture docs imply.

## First Things a Successor Will Hit

- Webhook deployment: local development is straightforward, but real inbound testing requires a stable public URL for Resend, Africa's Talking, and Cal.com.
- Data quality: the committed Crunchbase and layoffs datasets are samples and not guaranteed to contain the exact target firms used in documentation examples.
- Provider drift: email, SMS, and job-site selectors are all external integrations and are the most likely parts of the codebase to break first.
- State model: warm-lead transitions now live in `agent/channel_policy.py`; future channel rules should be added there instead of inside handlers.

## Recommended Next Steps

- Add a test suite for `agent/channel_policy.py`, `agent/enrichment.py`, and the competitor-gap schema contract.
- Decide whether production should remain MCP-with-REST-fallback or become MCP-only, then align deployment checks and docs to that choice.
- Wire real Langfuse and OpenTelemetry traces into `agent/main.py` so the architecture diagram matches the production path.
- Automate periodic snapshot collection so `data/job_post_snapshots.json` and `data/public_signal_catalog.json` become generated evidence rather than maintained fixtures.
