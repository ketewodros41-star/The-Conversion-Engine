"""
Tenacious Conversion Engine — Service Verification Script
Run this after filling in .env to confirm all 5 services are live.
Usage: python setup_verify.py
"""

import os
import sys
import asyncio
from datetime import datetime, timezone

# Load .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv optional; set env vars manually

PASS = "✅"
FAIL = "❌"
WARN = "⚠️ "
results = []


def check(name, ok, detail=""):
    icon = PASS if ok else FAIL
    msg = f"{icon} {name}"
    if detail:
        msg += f" — {detail}"
    results.append((ok, msg))
    print(msg)


# ── 1. Resend ───────────────────────────────────────────────
def verify_resend():
    try:
        import resend
        resend.api_key = os.environ["RESEND_API_KEY"]
        r = resend.Emails.send({
            "from": "onboarding@resend.dev",
            "to": [os.environ.get("STAFF_SINK_EMAIL", "test@example.com")],
            "subject": "[VERIFY] Tenacious Engine — Resend test",
            "text": f"Resend verification at {datetime.now(timezone.utc).isoformat()}",
        })
        check("Resend", bool(r.get("id")), f"message_id={r.get('id','none')}")
    except KeyError:
        check("Resend", False, "RESEND_API_KEY not set in .env")
    except Exception as e:
        check("Resend", False, str(e)[:80])


# ── 2. Africa's Talking ─────────────────────────────────────
def verify_at():
    try:
        import africastalking
        africastalking.initialize(
            username=os.environ.get("AT_USERNAME", "sandbox"),
            api_key=os.environ["AT_API_KEY"],
        )
        sms = africastalking.SMS
        r = sms.send(
            message="[VERIFY] Tenacious Engine AT test",
            recipients=[os.environ.get("STAFF_SINK_NUMBER", "+254700000000")],
        )
        ok = r.get("SMSMessageData", {}).get("Recipients", [{}])[0].get("status") == "Success"
        check("Africa's Talking", ok, str(r)[:80])
    except KeyError:
        check("Africa's Talking", False, "AT_API_KEY not set in .env")
    except Exception as e:
        check("Africa's Talking", False, str(e)[:80])


# ── 3. HubSpot ──────────────────────────────────────────────
def verify_hubspot():
    try:
        import httpx
        token = os.environ["HUBSPOT_ACCESS_TOKEN"]
        r = httpx.post(
            "https://api.hubapi.com/crm/v3/objects/contacts",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={"properties": {
                "email": f"verify-test-{int(datetime.now().timestamp())}@tenacious-verify.example.com",
                "firstname": "VERIFY",
                "lastname": "TEST",
                "company": "Tenacious Engine Verify",
            }},
            timeout=10,
        )
        ok = r.status_code in (200, 201)
        check("HubSpot", ok, f"status={r.status_code} id={r.json().get('id','none')}")
    except KeyError:
        check("HubSpot", False, "HUBSPOT_ACCESS_TOKEN not set in .env")
    except Exception as e:
        check("HubSpot", False, str(e)[:80])


# ── 4. Cal.com ──────────────────────────────────────────────
def verify_calcom():
    try:
        import httpx
        url = os.environ.get("CALCOM_URL", "http://localhost:3000")
        key = os.environ.get("CALCOM_API_KEY", "")
        r = httpx.get(
            f"{url}/api/v1/event-types",
            headers={"Authorization": f"Bearer {key}"},
            timeout=5,
        )
        ok = r.status_code == 200
        event_types = r.json().get("event_types", []) if ok else []
        check("Cal.com", ok, f"status={r.status_code} event_types={len(event_types)}")
    except Exception as e:
        check("Cal.com", False, str(e)[:80])


# ── 5. Langfuse ─────────────────────────────────────────────
def verify_langfuse():
    try:
        from langfuse import Langfuse
        lf = Langfuse(
            public_key=os.environ["LANGFUSE_PUBLIC_KEY"],
            secret_key=os.environ["LANGFUSE_SECRET_KEY"],
            host=os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com"),
        )
        trace = lf.trace(name="tenacious-verify-test", metadata={"verify": True})
        trace.score(name="verify", value=1.0)
        lf.flush()
        check("Langfuse", True, f"trace_id={trace.id}")
    except KeyError as e:
        check("Langfuse", False, f"{e} not set in .env")
    except Exception as e:
        check("Langfuse", False, str(e)[:80])


# ── 6. Data files ───────────────────────────────────────────
def verify_data():
    cb = os.path.exists("data/crunchbase_odm_sample.json")
    lf = os.path.exists("data/layoffs_fyi_snapshot.csv")
    check("Crunchbase ODM JSON", cb, "data/crunchbase_odm_sample.json")
    check("Layoffs.fyi CSV", lf, "data/layoffs_fyi_snapshot.csv")


# ── 7. tau2-bench ───────────────────────────────────────────
def verify_tau2bench():
    exists = os.path.isdir("tau2-bench") and any(
        os.path.exists(f"tau2-bench/{f}")
        for f in ["README.md", "tau2_bench", "src"]
    )
    check("tau2-bench cloned", exists, "tau2-bench/ directory")


if __name__ == "__main__":
    print("=" * 50)
    print("Tenacious Engine — Service Verification")
    print(f"Time: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 50)

    verify_data()
    verify_tau2bench()
    verify_resend()
    verify_at()
    verify_hubspot()
    verify_calcom()
    verify_langfuse()

    print("\n" + "=" * 50)
    passed = sum(1 for ok, _ in results if ok)
    total = len(results)
    print(f"Result: {passed}/{total} checks passed")
    if passed == total:
        print("✅ ALL SERVICES VERIFIED — ready for submission")
    else:
        failed = [msg for ok, msg in results if not ok]
        print("❌ Still needed:")
        for m in failed:
            print(f"   {m}")
    sys.exit(0 if passed == total else 1)
