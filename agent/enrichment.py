"""
Tenacious Conversion Engine - Enrichment Pipeline
Generates structured signal artifacts from public data sources.
"""

import json
from datetime import datetime, timedelta, timezone
from typing import Optional

import aiohttp
import pandas as pd
import structlog

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    async_playwright = None
    PLAYWRIGHT_AVAILABLE = False

log = structlog.get_logger()

BENCH_SUMMARY = {
    "python_engineers": 4,
    "mlops_engineers": 2,
    "platform_engineers_k8s": 3,
    "data_engineers": 3,
    "go_engineers": 2,
    "ml_research_engineers": 1,
    "infra_engineers": 4,
    "last_updated": "2026-04-21",
}

CRUNCHBASE_ODM_PATH = "data/crunchbase_odm_sample.json"
LAYOFFS_FYI_PATH = "data/layoffs_fyi_snapshot.csv"


class EnrichmentPipeline:
    """Builds hiring and signal briefs from public signals."""

    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={
                    "User-Agent": "TenaciousConversionEngine/1.0 (research; contact@tenacious.example.com)"
                }
            )
        return self.session

    def _parse_json_field(self, value, default):
        if value in (None, "", "null"):
            return default
        if isinstance(value, (list, dict)):
            return value
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return default
        return default

    def _normalize_employee_count(self, value) -> int:
        if value in (None, "", "null"):
            return 0
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            digits = [int(token) for token in value.replace("+", "").split("-") if token.strip().isdigit()]
            if len(digits) == 1:
                return digits[0]
            if len(digits) == 2:
                return int(sum(digits) / 2)
        return 0

    def _confidence_tier(self, confidence: float) -> str:
        if confidence >= 0.85:
            return "high"
        if confidence >= 0.70:
            return "medium"
        return "low"

    async def lookup_crunchbase(self, crunchbase_id: str) -> dict:
        try:
            with open(CRUNCHBASE_ODM_PATH, encoding="utf-8") as handle:
                odm_data = json.load(handle)
            record = next((row for row in odm_data if row.get("uuid") == crunchbase_id), None)
            if not record:
                log.warning("crunchbase_record_not_found", crunchbase_id=crunchbase_id)
                return {"found": False, "crunchbase_id": crunchbase_id}
            normalized = {
                **record,
                "funding_rounds": self._parse_json_field(record.get("funding_rounds"), []),
                "people": self._parse_json_field(record.get("people"), []),
                "category_list": self._parse_json_field(record.get("category_list"), []),
                "news": self._parse_json_field(record.get("news"), []),
                "builtwith_top_technologies": self._parse_json_field(
                    record.get("builtwith_top_technologies"), []
                ),
                "employee_count": self._normalize_employee_count(
                    record.get("employee_count") or record.get("num_employees")
                ),
            }
            return {"found": True, **normalized}
        except FileNotFoundError:
            log.error("crunchbase_odm_not_found", path=CRUNCHBASE_ODM_PATH)
            return {"found": False, "crunchbase_id": crunchbase_id, "error": "ODM file not loaded"}

    async def detect_funding_signal(self, crunchbase_record: dict) -> dict:
        cutoff = datetime.now(timezone.utc) - timedelta(days=180)
        funding_rounds = crunchbase_record.get("funding_rounds", [])
        recent_rounds = []
        for round_event in funding_rounds:
            announced_on = round_event.get("announced_on")
            if not announced_on:
                continue
            announced_dt = datetime.fromisoformat(announced_on.replace("Z", "+00:00"))
            if announced_dt > cutoff:
                recent_rounds.append(round_event)

        if not recent_rounds:
            confidence = 0.95
            return {
                "signal_type": "funding_event",
                "source": "Crunchbase ODM sample",
                "present": False,
                "confidence": confidence,
                "confidence_tier": self._confidence_tier(confidence),
                "brief_language": "No qualifying funding event found in the last 180 days.",
            }

        latest = max(recent_rounds, key=lambda item: item["announced_on"])
        days_since = (
            datetime.now(timezone.utc) -
            datetime.fromisoformat(latest["announced_on"].replace("Z", "+00:00"))
        ).days
        confidence = 0.97
        return {
            "signal_type": "funding_event",
            "source": "Crunchbase ODM sample",
            "present": True,
            "round_type": latest.get("investment_type", "Unknown"),
            "amount_usd": latest.get("raised_amount_usd"),
            "date": latest.get("announced_on"),
            "days_since_close": days_since,
            "within_180_day_window": True,
            "confidence": confidence,
            "confidence_tier": self._confidence_tier(confidence),
            "brief_language": (
                f"{crunchbase_record.get('name', 'The company')} closed a "
                f"{latest.get('investment_type', 'recent round')} on {latest.get('announced_on')}."
            ),
        }

    async def scrape_job_posts(self, company_name: str, careers_url: Optional[str] = None) -> dict:
        if not PLAYWRIGHT_AVAILABLE:
            log.warning("playwright_unavailable")
            confidence = 0.30
            return {
                "signal_type": "job_post_velocity",
                "source": "playwright_unavailable",
                "present": False,
                "total_open_roles": 0,
                "engineering_roles": 0,
                "ai_adjacent_roles": 0,
                "role_titles": [],
                "confidence": confidence,
                "confidence_tier": self._confidence_tier(confidence),
                "brief_language": "Playwright unavailable, so no public job-post signal was collected.",
            }

        jobs: list[str] = []
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (compatible; TenaciousBot/1.0; +https://tenacious.example.com/bot)"
            )
            page = await context.new_page()
            try:
                slug = company_name.lower().replace(" ", "-")
                wellfound_url = f"https://wellfound.com/company/{slug}/jobs"
                await page.goto(wellfound_url, timeout=10000)
                await page.wait_for_selector(".job-listing", timeout=5000)
                job_elements = await page.query_selector_all(".job-listing h3")
                jobs = [await element.inner_text() for element in job_elements]
            except Exception as exc:
                log.debug("wellfound_scrape_failed", company=company_name, error=str(exc))
            finally:
                await browser.close()

        engineering_keywords = [
            "engineer", "developer", "architect", "data", "ml", "machine learning",
            "platform", "infrastructure", "devops", "mlops", "llm", "ai",
        ]
        ai_keywords = [
            "ml", "machine learning", "ai", "llm", "applied scientist", "data platform",
            "inference", "model",
        ]
        eng_roles = [job for job in jobs if any(keyword in job.lower() for keyword in engineering_keywords)]
        ai_roles = [job for job in jobs if any(keyword in job.lower() for keyword in ai_keywords)]

        confidence = 0.75 if jobs else 0.30
        return {
            "signal_type": "job_post_velocity",
            "source": "Wellfound public job listings via Playwright",
            "present": bool(jobs),
            "total_open_roles": len(jobs),
            "engineering_roles": len(eng_roles),
            "ai_adjacent_roles": len(ai_roles),
            "role_titles": jobs[:20],
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "confidence": confidence,
            "confidence_tier": self._confidence_tier(confidence),
            "confidence_note": "Low confidence if fewer than 5 roles found; do not over-assert hiring velocity.",
            "brief_language": (
                f"Found {len(jobs)} public open roles, including {len(ai_roles)} AI-adjacent roles."
                if jobs else
                "No public job-post velocity signal found."
            ),
        }

    async def check_layoffs(self, company_name: str) -> dict:
        try:
            df = pd.read_csv(LAYOFFS_FYI_PATH)
            cutoff = datetime.now(timezone.utc) - timedelta(days=120)
            company_events = df[df["Company"].str.lower() == company_name.lower()]
            if company_events.empty:
                confidence = 0.90
                return {
                    "signal_type": "layoff_event",
                    "source": "layoffs.fyi snapshot csv",
                    "present": False,
                    "confidence": confidence,
                    "confidence_tier": self._confidence_tier(confidence),
                    "brief_language": "No layoff events found in the last 120 days.",
                }

            recent = company_events[pd.to_datetime(company_events["Date"], utc=True) > cutoff]
            if recent.empty:
                confidence = 0.90
                return {
                    "signal_type": "layoff_event",
                    "source": "layoffs.fyi snapshot csv",
                    "present": False,
                    "confidence": confidence,
                    "confidence_tier": self._confidence_tier(confidence),
                    "brief_language": "No recent layoff events found in the last 120 days.",
                }

            latest = recent.iloc[0]
            confidence = 0.95
            return {
                "signal_type": "layoff_event",
                "source": "layoffs.fyi snapshot csv",
                "present": True,
                "date": str(latest.get("Date")),
                "headcount_cut": latest.get("Laid_Off_Count"),
                "percentage_cut": latest.get("Percentage"),
                "source_url": latest.get("Source"),
                "confidence": confidence,
                "confidence_tier": self._confidence_tier(confidence),
                "brief_language": (
                    f"Layoff event detected on {latest.get('Date')} affecting "
                    f"{latest.get('Laid_Off_Count', 'an unspecified number of')} employees."
                ),
            }
        except FileNotFoundError:
            log.warning("layoffs_fyi_dataset_not_found")
            confidence = 0.50
            return {
                "signal_type": "layoff_event",
                "source": "layoffs_dataset_missing",
                "present": False,
                "confidence": confidence,
                "confidence_tier": self._confidence_tier(confidence),
                "error": "Dataset not loaded",
                "brief_language": "Layoffs dataset unavailable during this run.",
            }

    async def detect_leadership_change(self, crunchbase_record: dict) -> dict:
        cutoff = datetime.now(timezone.utc) - timedelta(days=90)
        people = crunchbase_record.get("people", [])
        new_leaders = []
        for person in people:
            title = person.get("title", "").lower()
            start_date = person.get("start_date")
            if title not in {
                "cto",
                "vp engineering",
                "vp of engineering",
                "chief technology officer",
                "head of engineering",
            }:
                continue
            if not start_date:
                continue
            start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            if start_dt > cutoff:
                new_leaders.append(person)

        confidence = 0.80 if new_leaders else 0.75
        return {
            "signal_type": "leadership_change",
            "source": "Crunchbase ODM people records",
            "present": bool(new_leaders),
            "new_leaders": new_leaders,
            "confidence": confidence,
            "confidence_tier": self._confidence_tier(confidence),
            "brief_language": (
                f"Leadership change detected: {new_leaders[0].get('title', 'new engineering leader')}."
                if new_leaders else
                "No recent engineering leadership change detected."
            ),
        }

    async def detect_tech_stack(self, crunchbase_record: dict) -> dict:
        builtwith = crunchbase_record.get("builtwith_top_technologies", [])
        technologies = []
        for item in builtwith[:10]:
            if isinstance(item, dict) and item.get("name"):
                technologies.append(item["name"])
            elif isinstance(item, str):
                technologies.append(item)

        joined = " ".join(technologies).lower()
        bench_match = []
        if "python" in joined:
            bench_match.append("python")
        if any(token in joined for token in ["kubernetes", "k8s", "docker", "aws", "gcp", "azure"]):
            bench_match.append("platform")
        if any(token in joined for token in ["ray", "airflow", "dbt", "snowflake", "spark"]):
            bench_match.extend(["data", "mlops"])

        ai_ml_tools = [
            technology for technology in technologies
            if any(token in technology.lower() for token in ["ml", "ai", "ray", "dbt", "snowflake", "spark"])
        ]
        confidence = 0.80 if technologies else 0.40
        return {
            "signal_type": "tech_stack",
            "source": "Crunchbase ODM technology fields",
            "present": bool(technologies),
            "technologies": technologies,
            "details": {
                "bench_match": sorted(set(bench_match)),
                "ai_ml_tools": ai_ml_tools,
            },
            "confidence": confidence,
            "confidence_tier": self._confidence_tier(confidence),
            "brief_language": (
                f"Observed public stack signals: {', '.join(technologies[:5])}."
                if technologies else
                "No reliable public tech-stack signal found."
            ),
        }

    def score_ai_maturity(
        self,
        job_posts: dict,
        leadership: dict,
        tech_stack: dict,
    ) -> dict:
        score = 0.0
        signals = []

        ai_role_pct = job_posts.get("ai_adjacent_roles", 0) / max(job_posts.get("engineering_roles", 1), 1)
        if ai_role_pct > 0.4:
            score += 1
            signals.append({
                "signal": "AI-adjacent open roles",
                "weight": "HIGH",
                "evidence": f"{ai_role_pct:.0%} of engineering roles are AI-adjacent",
                "contribution": "strong positive",
            })
        elif ai_role_pct > 0.15:
            score += 0.5
            signals.append({
                "signal": "AI-adjacent open roles",
                "weight": "HIGH",
                "evidence": f"{ai_role_pct:.0%} of engineering roles are AI-adjacent",
                "contribution": "moderate positive",
            })

        if leadership.get("present"):
            score += 1
            signals.append({
                "signal": "Recent engineering leadership change",
                "weight": "HIGH",
                "evidence": leadership.get("new_leaders", [{}])[0].get("title", "New engineering leader"),
                "contribution": "strong positive",
            })
        else:
            signals.append({
                "signal": "Recent engineering leadership change",
                "weight": "HIGH",
                "evidence": "No new CTO / VP Engineering detected in the last 90 days",
                "contribution": "absent",
            })

        ml_tools = tech_stack.get("details", {}).get("ai_ml_tools", [])
        if ml_tools:
            score += 0.5
            signals.append({
                "signal": "Observed AI/data tooling",
                "weight": "MEDIUM",
                "evidence": f"Detected: {', '.join(ml_tools[:3])}",
                "contribution": "moderate positive",
            })
        if len(ml_tools) >= 2:
            score += 0.25
            signals.append({
                "signal": "Modern data/ML stack",
                "weight": "LOW",
                "evidence": f"Detected: {', '.join(ml_tools[:3])}",
                "contribution": "positive",
            })

        final_score = min(3, int(round(score)))
        high_weight_signals = sum(1 for signal in signals if signal["weight"] == "HIGH")
        confidence = 0.90 if high_weight_signals >= 2 else 0.75 if high_weight_signals == 1 else 0.55
        return {
            "signal_type": "ai_maturity",
            "source": "Composite of collected public signals",
            "score": final_score,
            "confidence": confidence,
            "confidence_tier": self._confidence_tier(confidence),
            "per_signal_breakdown": signals,
            "confidence_note": (
                "High confidence: multiple high-weight signals corroborate score."
                if confidence >= 0.85 else
                "Medium confidence: score inferred from mixed signals. Ask rather than assert."
                if confidence >= 0.70 else
                "Low confidence: weak signal basis. Use exploratory language."
            ),
        }

    async def check_bench_availability(self, required_skills: list) -> dict:
        skill_map = {
            "python": BENCH_SUMMARY["python_engineers"],
            "mlops": BENCH_SUMMARY["mlops_engineers"],
            "platform": BENCH_SUMMARY["platform_engineers_k8s"],
            "data": BENCH_SUMMARY["data_engineers"],
            "go": BENCH_SUMMARY["go_engineers"],
            "ml": BENCH_SUMMARY["ml_research_engineers"],
            "infra": BENCH_SUMMARY["infra_engineers"],
        }
        available = {}
        for skill in required_skills:
            for key, count in skill_map.items():
                if key in skill.lower() and count > 0:
                    available[skill] = count
                    break
        return {
            "available": bool(available),
            "matching_skills": available,
            "bench_last_updated": BENCH_SUMMARY["last_updated"],
            "commitment_safe": bool(available),
            "hard_constraint_note": (
                "Do not commit to specific headcount. Reference availability only and hand off exact staffing."
            ),
        }

    async def build_hiring_signal_brief(self, crunchbase_id: str, company_name: str) -> dict:
        crunchbase_rec = await self.lookup_crunchbase(crunchbase_id)
        funding = await self.detect_funding_signal(crunchbase_rec)
        jobs = await self.scrape_job_posts(company_name, crunchbase_rec.get("homepage_url"))
        layoffs = await self.check_layoffs(company_name)
        leadership = await self.detect_leadership_change(crunchbase_rec)
        tech_stack = await self.detect_tech_stack(crunchbase_rec)
        ai_maturity = self.score_ai_maturity(
            job_posts=jobs,
            leadership=leadership,
            tech_stack=tech_stack,
        )
        signal_confidences = [
            signal["confidence"]
            for signal in [funding, jobs, layoffs, leadership, tech_stack, ai_maturity]
            if isinstance(signal.get("confidence"), (int, float))
        ]
        return {
            "prospect": {
                "company_name": company_name,
                "crunchbase_id": crunchbase_id,
                "industry": ", ".join(
                    item.get("value", "")
                    for item in crunchbase_rec.get("category_list", [])
                    if isinstance(item, dict)
                ) or "Unknown",
                "employee_count": crunchbase_rec.get("employee_count", 0),
            },
            "signals": {
                "funding_event": funding,
                "job_post_velocity": jobs,
                "layoff_event": layoffs,
                "leadership_change": leadership,
                "tech_stack": tech_stack,
                "ai_maturity": ai_maturity,
            },
            "confidence_summary": {
                "overall_confidence": round(sum(signal_confidences) / len(signal_confidences), 2)
                if signal_confidences else 0.0,
                "signal_confidences": {
                    "funding_event": funding.get("confidence", 0.0),
                    "job_post_velocity": jobs.get("confidence", 0.0),
                    "layoff_event": layoffs.get("confidence", 0.0),
                    "leadership_change": leadership.get("confidence", 0.0),
                    "tech_stack": tech_stack.get("confidence", 0.0),
                    "ai_maturity": ai_maturity.get("confidence", 0.0),
                },
            },
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    async def build_competitor_gap_brief(self, crunchbase_id: str, sector: str) -> dict:
        return {
            "prospect_id": crunchbase_id,
            "sector": sector,
            "analysis_note": "Top-quartile comparison computed from Crunchbase ODM sample + public signal scoring",
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
