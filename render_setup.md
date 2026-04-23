# Render Webhook Backend Setup

Your FastAPI server (`agent/main.py`) needs a stable public URL so Resend, Africa's Talking, Cal.com, and HubSpot can POST events to it. Render's free tier gives you this in under 10 minutes.

---

## 1. Create a Render Account

1. Go to **render.com** → Sign up with GitHub (fastest — no credit card needed)
2. Authorize Render to access your GitHub

---

## 2. Deploy the FastAPI App

1. Render dashboard → **New** → **Web Service**
2. Connect repo: `ketewodros41-star/The-Conversion-Engine`
3. Fill in settings:

| Field | Value |
|---|---|
| **Name** | `tenacious-conversion-engine` |
| **Region** | Frankfurt (EU) or Oregon (US) |
| **Branch** | `master` |
| **Runtime** | Python 3 |
| **Build Command** | `pip install -r agent/requirements.txt` |
| **Start Command** | `uvicorn agent.main:app --host 0.0.0.0 --port $PORT` |
| **Instance Type** | Free |

4. Click **Create Web Service**

Render will build and deploy. After ~2 minutes you get a URL like:
```
https://tenacious-conversion-engine.onrender.com
```
This is your **webhook base URL**. Copy it.

---

## 3. Set Environment Variables

In Render dashboard → your service → **Environment** → add each key from your `.env`:

```
LIVE_MODE=false
ANTHROPIC_API_KEY=...
OPENROUTER_API_KEY=...
RESEND_API_KEY=...
SENDER_EMAIL=...
SENDER_NAME=Tenacious Consulting
AT_USERNAME=sandbox
AT_API_KEY=...
AT_SENDER_ID=TENACIOUS
HUBSPOT_ACCESS_TOKEN=...
CALCOM_URL=https://api.cal.com
CALCOM_API_KEY=...
CALCOM_EVENT_TYPE_ID=1
LANGFUSE_PUBLIC_KEY=...
LANGFUSE_SECRET_KEY=...
LANGFUSE_HOST=https://cloud.langfuse.com
STAFF_SINK_EMAIL=ktewodros41@gmail.com
STAFF_SINK_NUMBER=+254700000000
```

> **Never paste your real keys into the repo — only into Render's dashboard.**

---

## 4. Register the Webhook URL with Each Service

Once deployed, register `https://tenacious-conversion-engine.onrender.com` as the webhook URL in all four services:

### Resend — Email Reply Handling
- Resend dashboard → **Webhooks** → Add endpoint
- URL: `https://tenacious-conversion-engine.onrender.com/webhook/email/inbound`
- Events: `email.delivered`, `email.bounced`, `email.complained`

### Africa's Talking — SMS Callbacks
- AT dashboard → **SMS** → **Shortcodes / Sender IDs** → your sender → **Callback URL**
- URL: `https://tenacious-conversion-engine.onrender.com/webhook/sms/inbound`

### Cal.com — Booking Events
- Cal.com → **Settings** → **Developer** → **Webhooks** → New webhook
- URL: `https://tenacious-conversion-engine.onrender.com/webhook/calcom`
- Events: `BOOKING_CREATED`, `BOOKING_CANCELLED`

### HubSpot — Contact Activity
- HubSpot → **Settings** → **Integrations** → **Private Apps** → your app → **Webhooks**
- URL: `https://tenacious-conversion-engine.onrender.com/webhook/hubspot`
- Subscriptions: `contact.creation`, `contact.propertyChange`

---

## 5. Verify It's Working

```bash
# Health check
curl https://tenacious-conversion-engine.onrender.com/health

# Expected response
{"status": "ok", "live_mode": false}
```

Check Render logs: dashboard → your service → **Logs** — you should see incoming POST requests when each service fires a test event.

---

## Notes

- **Free tier sleeps after 15 min of inactivity** — first request after sleep takes ~30s to wake up. This is fine for demos; upgrade to Starter ($7/mo) for production.
- **`LIVE_MODE=false`** keeps all outbound routed to your sink email/number even on Render. Only flip to `true` when Tenacious approves go-live.
- Render auto-redeploys on every push to `master` — no manual redeployment needed.
