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
PUBLIC_SIGNAL_CATALOG_PATH = "data/public_signal_catalog.json"
JOB_POST_SNAPSHOT_STORE_PATH = "data/job_post_snapshots.json"
JOB_HISTORY_WINDOW_DAYS = 60


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

    def _observed_at(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _source_attribution_from_news(self, items: list[dict]) -> list[str]:
        return [item.get("url") for item in items if isinstance(item, dict) and item.get("url")]

    def _load_public_signal_catalog(self) -> list[dict]:
        try:
            with open(PUBLIC_SIGNAL_CATALOG_PATH, encoding="utf-8") as handle:
                return json.load(handle)
        except FileNotFoundError:
            return []

    def _company_snapshot_key(self, company_name: str) -> str:
        return " ".join(company_name.strip().lower().split())

    def _load_job_snapshot_store(self) -> dict:
        try:
            with open(JOB_POST_SNAPSHOT_STORE_PATH, encoding="utf-8") as handle:
                data = json.load(handle)
            return data if isinstance(data, dict) else {}
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            log.warning("job_snapshot_store_invalid_json", path=JOB_POST_SNAPSHOT_STORE_PATH)
            return {}

    def _save_job_snapshot_store(self, store: dict) -> None:
        with open(JOB_POST_SNAPSHOT_STORE_PATH, "w", encoding="utf-8") as handle:
            json.dump(store, handle, indent=2)

    def _load_persisted_job_history(self, company_name: str) -> Optional[dict]:
        store = self._load_job_snapshot_store()
        entry = store.get(self._company_snapshot_key(company_name))
        if not isinstance(entry, dict):
            return None
        snapshots = entry.get("snapshots", [])
        if not isinstance(snapshots, list):
            return None
        return {
            "company_name": entry.get("company_name", company_name),
            "snapshots": snapshots,
        }

    def _persist_job_snapshot(
        self,
        *,
        company_name: str,
        source_attribution: list[str],
        role_titles: list[str],
        observed_at: str,
    ) -> None:
        store = self._load_job_snapshot_store()
        key = self._company_snapshot_key(company_name)
        entry = store.get(key, {"company_name": company_name, "snapshots": []})
        snapshots = entry.get("snapshots", [])
        new_snapshot = {
            "observed_at": observed_at,
            "open_roles": len(role_titles),
            "role_titles": role_titles,
            "source_attribution": source_attribution,
        }
        snapshots = [snapshot for snapshot in snapshots if snapshot.get("observed_at") != observed_at]
        snapshots.append(new_snapshot)
        snapshots = sorted(snapshots, key=lambda item: item.get("observed_at", ""))[-12:]
        entry["company_name"] = company_name
        entry["snapshots"] = snapshots
        store[key] = entry
        self._save_job_snapshot_store(store)

    def _merge_job_histories(self, *job_histories: Optional[dict]) -> Optional[dict]:
        merged_snapshots = []
        for history in job_histories:
            if not history:
                continue
            merged_snapshots.extend(history.get("snapshots", []))
        if not merged_snapshots:
            return None
        deduped = {
            snapshot.get("observed_at"): snapshot
            for snapshot in merged_snapshots
            if snapshot.get("observed_at")
        }
        return {
            "snapshots": sorted(deduped.values(), key=lambda item: item.get("observed_at", "")),
        }

    def _select_velocity_snapshot_pair(self, snapshots: list[dict]) -> tuple[Optional[dict], Optional[dict]]:
        if len(snapshots) < 2:
            return None, None
        latest = snapshots[-1]
        latest_observed_at = latest.get("observed_at")
        if not latest_observed_at:
            return None, None
        latest_dt = datetime.fromisoformat(latest_observed_at.replace("Z", "+00:00"))
        target_dt = latest_dt - timedelta(days=JOB_HISTORY_WINDOW_DAYS)
        previous_candidates = []
        for snapshot in snapshots[:-1]:
            observed_at = snapshot.get("observed_at")
            if not observed_at:
                continue
            snapshot_dt = datetime.fromisoformat(observed_at.replace("Z", "+00:00"))
            if snapshot_dt <= target_dt:
                previous_candidates.append((snapshot_dt, snapshot))
        if not previous_candidates:
            return latest, None
        previous = max(previous_candidates, key=lambda item: item[0])[1]
        return latest, previous

    def _find_catalog_record(
        self,
        *,
        crunchbase_id: Optional[str] = None,
        company_name: Optional[str] = None,
    ) -> Optional[dict]:
        company_name_norm = (company_name or "").strip().lower()
        for row in self._load_public_signal_catalog():
            if crunchbase_id and row.get("uuid") == crunchbase_id:
                return row
            if company_name_norm and row.get("name", "").strip().lower() == company_name_norm:
                return row
        return None

    def _normalize_company_record(self, record: dict) -> dict:
        return {
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

    def _role_titles_from_snapshot(self, snapshot: dict) -> list[str]:
        return [
            title.strip()
            for title in snapshot.get("role_titles", [])
            if isinstance(title, str) and title.strip()
        ]

    def _job_signal_from_history(self, company_name: str, job_history: Optional[dict]) -> Optional[dict]:
        if not job_history:
            return None
        snapshots = sorted(
            job_history.get("snapshots", []),
            key=lambda item: item.get("observed_at", ""),
        )
        latest, previous = self._select_velocity_snapshot_pair(snapshots)
        if not latest or not previous:
            return None
        deduped_jobs = list(dict.fromkeys(self._role_titles_from_snapshot(latest)))[:20]
        engineering_keywords = [
            "engineer", "developer", "architect", "data", "ml", "machine learning",
            "platform", "infrastructure", "devops", "mlops", "llm", "ai",
        ]
        ai_keywords = [
            "ml", "machine learning", "ai", "llm", "applied scientist", "data platform",
            "inference", "model",
        ]
        eng_roles = [
            job for job in deduped_jobs if any(keyword in job.lower() for keyword in engineering_keywords)
        ]
        ai_roles = [job for job in deduped_jobs if any(keyword in job.lower() for keyword in ai_keywords)]
        open_roles_today = int(latest.get("open_roles", len(deduped_jobs)))
        open_roles_60_days_ago = int(previous.get("open_roles", 0))
        velocity_delta = open_roles_today - open_roles_60_days_ago
        coverage = len(set(previous.get("source_attribution", [])) | set(latest.get("source_attribution", [])))
        confidence = 0.88 if coverage >= 2 else 0.80
        return {
            "signal_type": "job_post_velocity",
            "source": "Persisted public job-post snapshots",
            "present": bool(deduped_jobs),
            "observed_at": latest.get("observed_at"),
            "total_open_roles": open_roles_today,
            "engineering_roles": len(eng_roles),
            "ai_adjacent_roles": len(ai_roles),
            "open_roles_today": open_roles_today,
            "open_roles_60_days_ago": open_roles_60_days_ago,
            "velocity_delta_60_days": velocity_delta,
            "velocity_window_days": JOB_HISTORY_WINDOW_DAYS,
            "velocity_label": (
                "growing" if velocity_delta > 0 else
                "flat" if velocity_delta == 0 else
                "declining"
            ),
            "source_attribution": latest.get("source_attribution", []),
            "historical_snapshot_at": previous.get("observed_at"),
            "current_snapshot_at": latest.get("observed_at"),
            "role_titles": deduped_jobs,
            "scraped_at": latest.get("observed_at"),
            "confidence": confidence,
            "confidence_tier": self._confidence_tier(confidence),
            "confidence_note": (
                "Computed from persisted snapshots rather than inferred backfill."
            ),
            "brief_language": (
                f"Found {open_roles_today} public open roles versus {open_roles_60_days_ago} roles "
                f"{JOB_HISTORY_WINDOW_DAYS} days earlier, including {len(ai_roles)} AI-adjacent roles."
                if deduped_jobs else
                "No public job-post velocity signal found."
            ),
        }

    async def _check_robots_txt(self, domain: str, path: str = "/jobs") -> bool:
        """Checks robots.txt before scraping. Returns True if scraping is allowed.
        Only scrapes public pages; respects Disallow directives for our user-agent.
        Constraint: if robots.txt explicitly disallows the path for '*' or 'TenaciousBot',
        we skip the scrape entirely rather than proceeding."""
        robots_url = f"https://{domain}/robots.txt"
        try:
            session = await self._get_session()
            async with session.get(robots_url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status != 200:
                    return True  # No robots.txt: public pages are fair game
                content = await resp.text()
            in_relevant_block = False
            for line in content.splitlines():
                line = line.strip()
                if line.lower().startswith("user-agent:"):
                    agent = line.split(":", 1)[1].strip()
                    in_relevant_block = agent in ("*", "TenaciousBot")
                elif in_relevant_block and line.lower().startswith("disallow:"):
                    disallowed = line.split(":", 1)[1].strip()
                    if disallowed == "/" or (disallowed and path.startswith(disallowed)):
                        log.info("robots_txt_disallow", domain=domain, path=path, rule=disallowed)
                        return False
            return True
        except Exception:
            return True  # Network error: assume allowed, fall back to scraping

    async def lookup_crunchbase(self, crunchbase_id: str) -> dict:
        try:
            with open(CRUNCHBASE_ODM_PATH, encoding="utf-8") as handle:
                odm_data = json.load(handle)
            record = next((row for row in odm_data if row.get("uuid") == crunchbase_id), None)
            if not record:
                catalog_record = self._find_catalog_record(crunchbase_id=crunchbase_id)
                if catalog_record:
                    return {"found": True, **self._normalize_company_record(catalog_record)}
                log.warning("crunchbase_record_not_found", crunchbase_id=crunchbase_id)
                return {"found": False, "crunchbase_id": crunchbase_id}
            return {"found": True, **self._normalize_company_record(record)}
        except FileNotFoundError:
            log.error("crunchbase_odm_not_found", path=CRUNCHBASE_ODM_PATH)
            catalog_record = self._find_catalog_record(crunchbase_id=crunchbase_id)
            if catalog_record:
                return {"found": True, **self._normalize_company_record(catalog_record)}
            return {"found": False, "crunchbase_id": crunchbase_id, "error": "ODM file not loaded"}

    async def detect_funding_signal(self, crunchbase_record: dict) -> dict:
        cutoff = datetime.now(timezone.utc) - timedelta(days=180)
        observed_at = self._observed_at()
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
                "observed_at": observed_at,
                "source_attribution": [],
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
            "observed_at": observed_at,
            "round_type": latest.get("investment_type", "Unknown"),
            "amount_usd": latest.get("raised_amount_usd"),
            "date": latest.get("announced_on"),
            "days_since_close": days_since,
            "within_180_day_window": True,
            "source_attribution": [
                crunchbase_record.get("homepage_url"),
            ] if crunchbase_record.get("homepage_url") else [],
            "confidence": confidence,
            "confidence_tier": self._confidence_tier(confidence),
            "brief_language": (
                f"{crunchbase_record.get('name', 'The company')} closed a "
                f"{latest.get('investment_type', 'recent round')} on {latest.get('announced_on')}."
            ),
        }

    async def scrape_job_posts(self, company_name: str, careers_url: Optional[str] = None) -> dict:
        catalog_record = self._find_catalog_record(company_name=company_name)
        persisted_history = self._load_persisted_job_history(company_name)
        historical_signal = self._job_signal_from_history(
            company_name,
            self._merge_job_histories(
                catalog_record.get("job_history") if catalog_record else None,
                persisted_history,
            ),
        )
        if historical_signal:
            return historical_signal

        if not PLAYWRIGHT_AVAILABLE:
            log.warning("playwright_unavailable")
            confidence = 0.30
            return {
                "signal_type": "job_post_velocity",
                "source": "playwright_unavailable",
                "present": False,
                "observed_at": self._observed_at(),
                "total_open_roles": 0,
                "engineering_roles": 0,
                "ai_adjacent_roles": 0,
                "role_titles": [],
                "history_status": "insufficient_snapshots",
                "source_attribution": [],
                "confidence": confidence,
                "confidence_tier": self._confidence_tier(confidence),
                "brief_language": (
                    "Playwright unavailable, so no public job-post signal was collected and no "
                    "persisted 60-day velocity could be computed."
                ),
            }

        # Robots.txt compliance: check public-page permissions before launching the browser.
        # We target Wellfound, BuiltIn, and LinkedIn public pages. If a site blocks
        # robots or fails to load, we skip it rather than scraping around the control.
        slug = company_name.lower().replace(" ", "-")
        public_sources = [
            {
                "name": "wellfound",
                "domain": "wellfound.com",
                "path": f"/company/{slug}/jobs",
                "url": f"https://wellfound.com/company/{slug}/jobs",
                "selector": ".job-listing h3",
            },
            {
                "name": "builtin",
                "domain": "builtin.com",
                "path": f"/company/{slug}/jobs",
                "url": f"https://builtin.com/company/{slug}/jobs",
                "selector": "h2, h3[data-id='job-title'], a[data-id='job-title']",
            },
            {
                "name": "linkedin_public",
                "domain": "linkedin.com",
                "path": f"/company/{slug}/jobs",
                "url": f"https://www.linkedin.com/company/{slug}/jobs/",
                "selector": ".jobs-search__results-list h3, .base-search-card__title",
            },
        ]

        jobs: list[str] = []
        source_attribution: list[str] = []
        try:
            async with async_playwright() as playwright:
                browser = await playwright.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (compatible; TenaciousBot/1.0; +https://tenacious.example.com/bot)"
                )
                try:
                    for source in public_sources:
                        allowed = await self._check_robots_txt(source["domain"], source["path"])
                        if not allowed:
                            log.info("robots_txt_blocked_jobs_source", company=company_name, source=source["name"])
                            continue
                        page = await context.new_page()
                        try:
                            await page.goto(source["url"], timeout=10000)
                            await page.wait_for_timeout(1500)
                            job_elements = await page.query_selector_all(source["selector"])
                            source_jobs = []
                            for element in job_elements[:20]:
                                text = (await element.inner_text()).strip()
                                if text and len(text) < 150:
                                    source_jobs.append(text)
                            if source_jobs:
                                jobs.extend(source_jobs)
                                source_attribution.append(source["url"])
                        except Exception as exc:
                            log.debug(
                                "public_job_scrape_failed",
                                company=company_name,
                                source=source["name"],
                                error=str(exc),
                            )
                        finally:
                            await page.close()
                finally:
                    await browser.close()
        except Exception as exc:
            log.warning("playwright_scrape_failed", error=str(exc))

        deduped_jobs = list(dict.fromkeys(jobs))[:20]
        engineering_keywords = [
            "engineer", "developer", "architect", "data", "ml", "machine learning",
            "platform", "infrastructure", "devops", "mlops", "llm", "ai",
        ]
        ai_keywords = [
            "ml", "machine learning", "ai", "llm", "applied scientist", "data platform",
            "inference", "model",
        ]
        eng_roles = [
            job for job in deduped_jobs if any(keyword in job.lower() for keyword in engineering_keywords)
        ]
        ai_roles = [job for job in deduped_jobs if any(keyword in job.lower() for keyword in ai_keywords)]
        observed_at = datetime.now(timezone.utc).isoformat()
        self._persist_job_snapshot(
            company_name=company_name,
            source_attribution=source_attribution,
            role_titles=deduped_jobs,
            observed_at=observed_at,
        )
        merged_history = self._merge_job_histories(
            catalog_record.get("job_history") if catalog_record else None,
            self._load_persisted_job_history(company_name),
        )
        historical_signal = self._job_signal_from_history(company_name, merged_history)
        if historical_signal:
            return historical_signal

        confidence = 0.82 if deduped_jobs and len(source_attribution) >= 2 else 0.75 if deduped_jobs else 0.30
        return {
            "signal_type": "job_post_velocity",
            "source": "Public job listings via Playwright",
            "present": bool(deduped_jobs),
            "observed_at": observed_at,
            "total_open_roles": len(deduped_jobs),
            "engineering_roles": len(eng_roles),
            "ai_adjacent_roles": len(ai_roles),
            "open_roles_today": len(deduped_jobs),
            "open_roles_60_days_ago": None,
            "velocity_delta_60_days": None,
            "velocity_window_days": JOB_HISTORY_WINDOW_DAYS,
            "velocity_label": "insufficient_history",
            "history_status": "insufficient_snapshots",
            "source_attribution": source_attribution,
            "role_titles": deduped_jobs,
            "historical_snapshot_at": None,
            "current_snapshot_at": observed_at,
            "scraped_at": observed_at,
            "confidence": confidence,
            "confidence_tier": self._confidence_tier(confidence),
            "confidence_note": (
                "A true 60-day velocity is only emitted after two persisted snapshots exist. "
                "Until then, use current open-role count as a point-in-time signal only."
            ),
            "brief_language": (
                f"Found {len(deduped_jobs)} public open roles today, including {len(ai_roles)} AI-adjacent roles. "
                f"A {JOB_HISTORY_WINDOW_DAYS}-day velocity delta will be emitted after a second persisted snapshot exists."
                if deduped_jobs else
                "No public job-post velocity signal found."
            ),
        }

    async def check_layoffs(self, company_name: str) -> dict:
        observed_at = self._observed_at()
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
                    "observed_at": observed_at,
                    "source_attribution": [],
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
                    "observed_at": observed_at,
                    "source_attribution": [],
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
                "observed_at": observed_at,
                "date": str(latest.get("Date")),
                "headcount_cut": latest.get("Laid_Off_Count"),
                "percentage_cut": latest.get("Percentage"),
                "source_url": latest.get("Source"),
                "source_attribution": [latest.get("Source")] if latest.get("Source") else [],
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
                "observed_at": observed_at,
                "source_attribution": [],
                "confidence": confidence,
                "confidence_tier": self._confidence_tier(confidence),
                "error": "Dataset not loaded",
                "brief_language": "Layoffs dataset unavailable during this run.",
            }

    async def detect_leadership_change(self, crunchbase_record: dict) -> dict:
        cutoff = datetime.now(timezone.utc) - timedelta(days=90)
        people = crunchbase_record.get("people", [])
        news = crunchbase_record.get("news", [])
        leadership_titles = {
            "cto",
            "vp engineering",
            "vp of engineering",
            "chief technology officer",
            "head of engineering",
            "head of ai",
            "vp ai",
            "vp of ai",
            "vp machine learning",
            "head of ml",
            "chief ai officer",
            "vp data",
            "vp of data",
            "head of data platform",
        }
        new_leaders = []
        for person in people:
            title = person.get("title", "").lower()
            start_date = person.get("start_date")
            if title not in leadership_titles:
                continue
            if not start_date:
                continue
            start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            if start_dt > cutoff:
                new_leaders.append(person)

        for item in news:
            if not isinstance(item, dict):
                continue
            published_at = item.get("published_at") or item.get("date")
            if not published_at:
                continue
            try:
                published_dt = datetime.fromisoformat(str(published_at).replace("Z", "+00:00"))
            except ValueError:
                continue
            if published_dt <= cutoff:
                continue
            combined_text = " ".join([
                str(item.get("title", "")),
                str(item.get("description", "")),
            ]).lower()
            if "hired" not in combined_text and "appointed" not in combined_text and "named" not in combined_text:
                continue
            matched_title = next((title for title in leadership_titles if title in combined_text), None)
            if not matched_title:
                continue
            new_leaders.append({
                "title": matched_title.title(),
                "start_date": published_dt.isoformat(),
                "source_url": item.get("url"),
                "source": "public_news",
            })

        confidence = 0.80 if new_leaders else 0.75
        observed_at = self._observed_at()
        return {
            "signal_type": "leadership_change",
            "source": "Crunchbase ODM people records and public news",
            "present": bool(new_leaders),
            "observed_at": observed_at,
            "new_leaders": new_leaders,
            "source_attribution": [
                leader.get("source_url") for leader in new_leaders if leader.get("source_url")
            ][:3],
            "confidence": confidence,
            "confidence_tier": self._confidence_tier(confidence),
            "brief_language": (
                f"Leadership change detected: {new_leaders[0].get('title', 'new engineering leader')}."
                if new_leaders else
                "No recent engineering leadership change detected."
            ),
        }

    async def detect_ai_leadership_presence(self, crunchbase_record: dict) -> dict:
        """
        Collects named AI/ML leadership independent of recent leadership-change detection.
        This closes the gap between "recent engineering transition" and "public AI leadership exists".
        """
        observed_at = self._observed_at()
        people = crunchbase_record.get("people", [])
        news = crunchbase_record.get("news", [])
        leadership_titles = {
            "head of ai",
            "vp ai",
            "vp of ai",
            "chief ai officer",
            "head of machine learning",
            "vp machine learning",
            "director of machine learning",
            "head of ml",
            "head of ml platform",
            "vp data",
            "vp of data",
            "chief data officer",
            "head of data science",
            "director of data science",
            "ai lead",
            "ml lead",
        }

        matched_people = []
        for person in people:
            title = str(person.get("title", "")).strip()
            title_lower = title.lower()
            if title_lower in leadership_titles:
                matched_people.append({
                    "name": person.get("name", ""),
                    "title": title,
                    "start_date": person.get("start_date"),
                    "source_url": person.get("source_url") or crunchbase_record.get("homepage_url", ""),
                    "source": "people_record",
                })

        matched_news = []
        for item in news:
            if not isinstance(item, dict):
                continue
            combined_text = " ".join([
                str(item.get("title", "")),
                str(item.get("description", "")),
            ]).lower()
            matched_title = next((title for title in leadership_titles if title in combined_text), None)
            if not matched_title:
                continue
            matched_news.append({
                "name": item.get("organization", ""),
                "title": matched_title.title(),
                "start_date": item.get("published_at") or item.get("date"),
                "source_url": item.get("url", ""),
                "source": "public_news",
            })

        leaders = []
        seen = set()
        for leader in matched_people + matched_news:
            dedupe_key = (leader.get("title", "").lower(), leader.get("source_url", ""))
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            leaders.append(leader)

        confidence = 0.85 if leaders else 0.70
        return {
            "signal_type": "ai_leadership",
            "source": "Crunchbase ODM people records and public news",
            "present": bool(leaders),
            "observed_at": observed_at,
            "leaders": leaders,
            "source_attribution": [
                leader.get("source_url") for leader in leaders if leader.get("source_url")
            ][:5],
            "confidence": confidence,
            "confidence_tier": self._confidence_tier(confidence),
            "brief_language": (
                f"Named AI/ML leadership detected: {leaders[0].get('title', 'AI leadership')}."
                if leaders else
                "No named AI/ML leadership detected in available public records."
            ),
        }

    async def detect_tech_stack(self, crunchbase_record: dict) -> dict:
        builtwith = crunchbase_record.get("builtwith_top_technologies", [])
        observed_at = self._observed_at()
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
            "observed_at": observed_at,
            "technologies": technologies,
            "source_url": crunchbase_record.get("homepage_url", ""),
            "source_attribution": [crunchbase_record.get("homepage_url")] if crunchbase_record.get("homepage_url") else [],
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

    async def check_github_activity(self, crunchbase_record: dict) -> dict:
        """Checks for public GitHub org activity. MEDIUM weight AI maturity signal."""
        observed_at = self._observed_at()
        github_url = crunchbase_record.get("github_url") or crunchbase_record.get("web_path_gh")
        news = crunchbase_record.get("news", [])
        builtwith = crunchbase_record.get("builtwith_top_technologies", [])
        tech_names = " ".join(
            item.get("name", "") if isinstance(item, dict) else str(item)
            for item in builtwith
        ).lower()

        github_news = [
            {
                "title": item.get("title"),
                "date": item.get("published_at"),
                "url": item.get("url"),
            }
            for item in news
            if isinstance(item, dict) and any(
                kw in str(item.get("title", "")).lower() or kw in str(item.get("description", "")).lower()
                for kw in ("github", "open source", "open-source", "repository", "repo", "open sourced")
            )
        ]
        has_tech_signal = "github" in tech_names

        if not github_url and not has_tech_signal and not github_news:
            confidence = 0.50
            return {
                "signal_type": "github_activity",
                "source": "Crunchbase ODM technology and news fields",
                "present": False,
                "observed_at": observed_at,
                "inference_basis": "No GitHub URL or open-source signal found in public records",
                "source_attribution": [],
                "confidence": confidence,
                "confidence_tier": self._confidence_tier(confidence),
                "brief_language": "No public GitHub org activity detected in available records.",
            }

        confidence = 0.75 if github_url else 0.60
        return {
            "signal_type": "github_activity",
            "source": "Crunchbase ODM technology and news fields",
            "present": True,
            "observed_at": observed_at,
            "github_url": github_url,
            "open_source_news_mentions": len(github_news),
            "inference_basis": (
                f"GitHub URL on record: {github_url}" if github_url else
                f"{len(github_news)} news mention(s) reference open-source or GitHub activity"
            ),
            "source_attribution": ([github_url] if github_url else []) + self._source_attribution_from_news(github_news),
            "confidence": confidence,
            "confidence_tier": self._confidence_tier(confidence),
            "brief_language": (
                f"Public GitHub org activity detected{(': ' + github_url) if github_url else ' via open-source news mentions'}."
            ),
        }

    async def check_exec_commentary(self, crunchbase_record: dict) -> dict:
        """Checks for executive public commentary on AI/ML/tech strategy. MEDIUM weight signal."""
        observed_at = self._observed_at()
        news = crunchbase_record.get("news", [])
        ai_keywords = [
            "ai", "machine learning", "ml", "llm", "artificial intelligence",
            "data platform", "foundation model", "generative ai", "deep learning",
            "model training", "inference", "ai-native", "ai strategy",
        ]
        ai_commentary = [
            {
                "title": item.get("title"),
                "date": item.get("published_at"),
                "url": item.get("url"),
            }
            for item in news
            if isinstance(item, dict) and any(
                kw in str(item.get("title", "")).lower() or kw in str(item.get("description", "")).lower()
                for kw in ai_keywords
            )
        ]

        if not ai_commentary:
            confidence = 0.75
            return {
                "signal_type": "exec_commentary",
                "source": "Crunchbase ODM news records",
                "present": False,
                "observed_at": observed_at,
                "items_found": 0,
                "sample_items": [],
                "source_attribution": [],
                "confidence": confidence,
                "confidence_tier": self._confidence_tier(confidence),
                "brief_language": "No public executive commentary on AI/ML strategy found in news records.",
            }

        confidence = 0.82
        return {
            "signal_type": "exec_commentary",
            "source": "Crunchbase ODM news records",
            "present": True,
            "observed_at": observed_at,
            "items_found": len(ai_commentary),
            "sample_items": ai_commentary[:3],
            "source_attribution": self._source_attribution_from_news(ai_commentary[:3]),
            "confidence": confidence,
            "confidence_tier": self._confidence_tier(confidence),
            "brief_language": (
                f"Found {len(ai_commentary)} public news item(s) with executive AI/ML commentary."
            ),
        }

    async def check_strategic_communications(self, crunchbase_record: dict) -> dict:
        """Checks for strategic communications: press releases, investor letters, conference talks.
        LOW weight AI maturity signal — presence alone does not indicate AI capability,
        only that the company communicates strategy publicly."""
        observed_at = self._observed_at()
        news = crunchbase_record.get("news", [])
        strategy_keywords = [
            "strategy", "roadmap", "vision", "partnership", "integration",
            "platform", "ecosystem", "launch", "announces", "introduces",
            "investor", "conference", "keynote", "summit",
        ]
        strategy_items = [
            {
                "title": item.get("title"),
                "date": item.get("published_at"),
                "url": item.get("url"),
            }
            for item in news
            if isinstance(item, dict) and any(
                kw in str(item.get("title", "")).lower()
                for kw in strategy_keywords
            )
        ]

        confidence = 0.68 if strategy_items else 0.60
        return {
            "signal_type": "strategic_communications",
            "source": "Crunchbase ODM news records",
            "present": bool(strategy_items),
            "observed_at": observed_at,
            "items_found": len(strategy_items),
            "sample_items": strategy_items[:3],
            "source_attribution": self._source_attribution_from_news(strategy_items[:3]),
            "confidence": confidence,
            "confidence_tier": self._confidence_tier(confidence),
            "brief_language": (
                f"Found {len(strategy_items)} strategic communications in public records."
                if strategy_items else
                "No strategic communications found in public news records."
            ),
        }

    def score_ai_maturity(
        self,
        job_posts: dict,
        ai_leadership: dict,
        tech_stack: dict,
        github_activity: Optional[dict] = None,
        exec_commentary: Optional[dict] = None,
        strategic_comms: Optional[dict] = None,
    ) -> dict:
        """
        Scores AI maturity 0–3 from six weighted signal categories.
        HIGH weight:   AI-adjacent open roles, named AI/ML leadership.
        MEDIUM weight: Public GitHub org activity, executive commentary on AI/ML.
        LOW weight:    Modern data/ML stack, strategic communications.

        Returns Score 0 with an explicit 'absence_not_proof_of_absence' flag
        when no public signals are found across all six categories.
        """
        score = 0.0
        signals = []

        # --- HIGH WEIGHT: AI-adjacent open roles ---
        ai_role_pct = job_posts.get("ai_adjacent_roles", 0) / max(job_posts.get("engineering_roles", 1), 1)
        if ai_role_pct > 0.4:
            score += 1.0
            signals.append({
                "signal": "AI-adjacent open roles",
                "weight": "HIGH",
                "evidence": f"{ai_role_pct:.0%} of engineering roles are AI-adjacent",
                "source_url": (job_posts.get("source_attribution") or [""])[0],
                "signal_confidence": job_posts.get("confidence"),
                "contribution": "strong positive",
            })
        elif ai_role_pct > 0.15:
            score += 0.5
            signals.append({
                "signal": "AI-adjacent open roles",
                "weight": "HIGH",
                "evidence": f"{ai_role_pct:.0%} of engineering roles are AI-adjacent",
                "source_url": (job_posts.get("source_attribution") or [""])[0],
                "signal_confidence": job_posts.get("confidence"),
                "contribution": "moderate positive",
            })
        else:
            signals.append({
                "signal": "AI-adjacent open roles",
                "weight": "HIGH",
                "evidence": "Fewer than 15% of engineering roles are AI-adjacent, or no job data available",
                "source_url": (job_posts.get("source_attribution") or [""])[0],
                "signal_confidence": job_posts.get("confidence"),
                "contribution": "absent",
            })

        # --- HIGH WEIGHT: Named AI/ML leadership ---
        if ai_leadership.get("present"):
            score += 1.0
            leader = ai_leadership.get("leaders", [{}])[0]
            signals.append({
                "signal": "Named AI/ML leadership",
                "weight": "HIGH",
                "evidence": f"Named AI/ML leader in public records: {leader.get('title', 'AI/ML leader')}",
                "source_url": leader.get("source_url") or (ai_leadership.get("source_attribution") or [""])[0],
                "signal_confidence": ai_leadership.get("confidence"),
                "contribution": "strong positive",
            })
        else:
            signals.append({
                "signal": "Named AI/ML leadership",
                "weight": "HIGH",
                "evidence": "No named Head of AI, VP Data, or recent CTO/VP Eng change detected in public records",
                "source_url": (ai_leadership.get("source_attribution") or [""])[0],
                "signal_confidence": ai_leadership.get("confidence"),
                "contribution": "absent",
            })

        # --- MEDIUM WEIGHT: Public GitHub org activity ---
        if github_activity and github_activity.get("present"):
            score += 0.5
            signals.append({
                "signal": "Public GitHub org activity",
                "weight": "MEDIUM",
                "evidence": github_activity.get("inference_basis", "GitHub activity detected"),
                "source_url": github_activity.get("github_url", ""),
                "signal_confidence": github_activity.get("confidence"),
                "contribution": "moderate positive",
            })
        else:
            signals.append({
                "signal": "Public GitHub org activity",
                "weight": "MEDIUM",
                "evidence": "No public GitHub org activity detected in available records",
                "source_url": github_activity.get("github_url", "") if github_activity else "",
                "signal_confidence": github_activity.get("confidence") if github_activity else None,
                "contribution": "absent",
            })

        # --- MEDIUM WEIGHT: Executive commentary on AI/ML ---
        if exec_commentary and exec_commentary.get("present"):
            score += 0.5
            signals.append({
                "signal": "Executive commentary on AI/ML",
                "weight": "MEDIUM",
                "evidence": (
                    f"{exec_commentary.get('items_found', 0)} public news item(s) with AI/ML commentary"
                ),
                "source_url": (exec_commentary.get("sample_items") or [{}])[0].get("url", ""),
                "signal_confidence": exec_commentary.get("confidence"),
                "contribution": "moderate positive",
            })
        else:
            signals.append({
                "signal": "Executive commentary on AI/ML",
                "weight": "MEDIUM",
                "evidence": "No public executive AI/ML commentary found in news records",
                "source_url": (exec_commentary.get("sample_items") or [{}])[0].get("url", "") if exec_commentary else "",
                "signal_confidence": exec_commentary.get("confidence") if exec_commentary else None,
                "contribution": "absent",
            })

        # --- LOW WEIGHT: Modern data/ML stack ---
        ml_tools = tech_stack.get("details", {}).get("ai_ml_tools", [])
        if ml_tools:
            score += 0.5
            signals.append({
                "signal": "Modern data/ML stack",
                "weight": "LOW",
                "evidence": f"Detected: {', '.join(ml_tools[:3])}",
                "source_url": tech_stack.get("source_url", ""),
                "signal_confidence": tech_stack.get("confidence"),
                "contribution": "positive",
            })
            if len(ml_tools) >= 2:
                score += 0.25
        else:
            signals.append({
                "signal": "Modern data/ML stack",
                "weight": "LOW",
                "evidence": "No AI/ML tooling detected in public stack records",
                "source_url": tech_stack.get("source_url", ""),
                "signal_confidence": tech_stack.get("confidence"),
                "contribution": "absent",
            })

        # --- LOW WEIGHT: Strategic communications ---
        if strategic_comms and strategic_comms.get("present"):
            score += 0.25
            signals.append({
                "signal": "Strategic communications",
                "weight": "LOW",
                "evidence": (
                    f"{strategic_comms.get('items_found', 0)} strategic communication(s) in public records"
                ),
                "source_url": (strategic_comms.get("sample_items") or [{}])[0].get("url", ""),
                "signal_confidence": strategic_comms.get("confidence"),
                "contribution": "positive",
            })
        else:
            signals.append({
                "signal": "Strategic communications",
                "weight": "LOW",
                "evidence": "No strategic communications found in public news records",
                "source_url": (strategic_comms.get("sample_items") or [{}])[0].get("url", "") if strategic_comms else "",
                "signal_confidence": strategic_comms.get("confidence") if strategic_comms else None,
                "contribution": "absent",
            })

        # --- Silent company handling ---
        # If no signal from any of the six categories is positive, return Score 0
        # with an explicit note that public absence is not proof of capability absence.
        any_signal_present = any(s.get("contribution") not in ("absent", None) for s in signals)
        if not any_signal_present:
            return {
                "signal_type": "ai_maturity",
                "source": "Composite of collected public signals",
                "score": 0,
                "absence_not_proof_of_absence": True,
                "observed_at": self._observed_at(),
                "source_attribution": [
                    signal.get("source_url", "") for signal in signals if signal.get("source_url")
                ],
                "confidence": 0.40,
                "confidence_tier": "low",
                "per_signal_breakdown": signals,
                "confidence_note": (
                    "Score 0 returned because no public signals were found across all six categories. "
                    "Absence of public signals is not proof of absence of capability — "
                    "the company may have significant internal AI investment not visible from public sources. "
                    "Use exploratory language rather than asserting low AI maturity."
                ),
            }

        final_score = min(3, int(round(score)))
        high_present = sum(1 for s in signals if s["weight"] == "HIGH" and s.get("contribution") != "absent")
        medium_present = sum(1 for s in signals if s["weight"] == "MEDIUM" and s.get("contribution") != "absent")

        if high_present >= 2:
            confidence = 0.90
        elif high_present == 1 and medium_present >= 1:
            confidence = 0.78
        elif high_present == 1:
            confidence = 0.72
        else:
            confidence = 0.55

        return {
            "signal_type": "ai_maturity",
            "source": "Composite of collected public signals",
            "score": final_score,
            "absence_not_proof_of_absence": False,
            "observed_at": self._observed_at(),
            "source_attribution": [
                signal.get("source_url", "") for signal in signals if signal.get("source_url")
            ],
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

    async def _build_company_signal_set(self, record: dict) -> dict:
        company_name = record.get("name", "Unknown")
        funding = await self.detect_funding_signal(record)
        jobs = (
            self._job_signal_from_history(company_name, record.get("job_history"))
            or await self.scrape_job_posts(company_name, record.get("homepage_url"))
        )
        layoffs = await self.check_layoffs(company_name)
        leadership = await self.detect_leadership_change(record)
        ai_leadership = await self.detect_ai_leadership_presence(record)
        tech_stack = await self.detect_tech_stack(record)
        github_activity = await self.check_github_activity(record)
        exec_commentary = await self.check_exec_commentary(record)
        strategic_comms = await self.check_strategic_communications(record)
        ai_maturity = self.score_ai_maturity(
            job_posts=jobs,
            ai_leadership=ai_leadership,
            tech_stack=tech_stack,
            github_activity=github_activity,
            exec_commentary=exec_commentary,
            strategic_comms=strategic_comms,
        )
        return {
            "funding_event": funding,
            "job_post_velocity": jobs,
            "layoff_event": layoffs,
            "leadership_change": leadership,
            "ai_leadership": ai_leadership,
            "tech_stack": tech_stack,
            "github_activity": github_activity,
            "exec_commentary": exec_commentary,
            "strategic_communications": strategic_comms,
            "ai_maturity": ai_maturity,
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

    def _infer_gap_findings(self, prospect_ai_score: int, selected_competitors: list[dict]) -> list[dict]:
        gap_findings = []

        leadership_evidence = [
            {
                "competitor_name": competitor["name"],
                "evidence": breakdown["evidence"],
                "source_url": breakdown.get("source_url", ""),
            }
            for competitor in selected_competitors
            for breakdown in competitor.get("ai_maturity_breakdown", [])
            if breakdown.get("signal") == "Named AI/ML leadership"
            and breakdown.get("contribution") not in ("absent", None)
        ][:4]
        if leadership_evidence and prospect_ai_score < 3:
            gap_findings.append({
                "gap_name": "Dedicated AI leadership",
                "practice": "Dedicated AI/ML leadership at executive or VP level",
                "business_implication": "Peers are formalizing AI ownership earlier, which usually speeds platform and hiring decisions.",
                "confidence": 0.88,
                "evidence_fields": leadership_evidence,
            })

        eval_evidence = [
            {
                "competitor_name": competitor["name"],
                "evidence": breakdown["evidence"],
                "source_url": breakdown.get("source_url", ""),
            }
            for competitor in selected_competitors
            for breakdown in competitor.get("ai_maturity_breakdown", [])
            if breakdown.get("signal") in {"Public GitHub org activity", "Executive commentary on AI/ML"}
            and breakdown.get("contribution") not in ("absent", None)
        ][:4]
        if eval_evidence:
            gap_findings.append({
                "gap_name": "Public evaluation discipline",
                "practice": "Structured model evaluation or public evidence of eval tooling",
                "business_implication": "Peers signal stronger production AI discipline when they show evaluation workflows or related tooling.",
                "confidence": 0.74,
                "evidence_fields": eval_evidence,
            })

        platform_evidence = [
            {
                "competitor_name": competitor["name"],
                "evidence": breakdown["evidence"],
                "source_url": breakdown.get("source_url", ""),
            }
            for competitor in selected_competitors
            for breakdown in competitor.get("ai_maturity_breakdown", [])
            if breakdown.get("signal") == "Modern data/ML stack"
            and breakdown.get("contribution") not in ("absent", None)
        ][:4]
        if platform_evidence:
            gap_findings.append({
                "gap_name": "Production data and ML platform stack",
                "practice": "Publicly visible data platform or ML platform operating practices",
                "business_implication": "Peers are signaling more mature data and platform foundations for AI delivery.",
                "confidence": 0.83,
                "evidence_fields": platform_evidence,
            })

        return gap_findings[:3]

    async def build_hiring_signal_brief(self, crunchbase_id: str, company_name: str) -> dict:
        crunchbase_rec = await self.lookup_crunchbase(crunchbase_id)
        if not crunchbase_rec.get("found"):
            fallback = self._find_catalog_record(company_name=company_name)
            if fallback:
                crunchbase_rec = {"found": True, **self._normalize_company_record(fallback)}
        signals = await self._build_company_signal_set(crunchbase_rec)
        signal_confidences = [
            signal["confidence"]
            for signal in [
                signals["funding_event"],
                signals["job_post_velocity"],
                signals["layoff_event"],
                signals["leadership_change"],
                signals["ai_leadership"],
                signals["tech_stack"],
                signals["ai_maturity"],
            ]
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
            "signals": signals,
            "confidence_summary": {
                "overall_confidence": round(sum(signal_confidences) / len(signal_confidences), 2)
                if signal_confidences else 0.0,
                "signal_confidences": {
                    "funding_event": signals["funding_event"].get("confidence", 0.0),
                    "job_post_velocity": signals["job_post_velocity"].get("confidence", 0.0),
                    "layoff_event": signals["layoff_event"].get("confidence", 0.0),
                    "leadership_change": signals["leadership_change"].get("confidence", 0.0),
                    "ai_leadership": signals["ai_leadership"].get("confidence", 0.0),
                    "tech_stack": signals["tech_stack"].get("confidence", 0.0),
                    "github_activity": signals["github_activity"].get("confidence", 0.0),
                    "exec_commentary": signals["exec_commentary"].get("confidence", 0.0),
                    "strategic_communications": signals["strategic_communications"].get("confidence", 0.0),
                    "ai_maturity": signals["ai_maturity"].get("confidence", 0.0),
                },
            },
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    async def build_competitor_gap_brief(
        self,
        crunchbase_id: str,
        sector: str,
        prospect_ai_score: Optional[int] = None,
    ) -> dict:
        """
        Identifies 5-10 top-quartile competitors in the prospect's sector,
        scores each with the same AI maturity framework applied to the prospect,
        computes the prospect's distribution position in the sector, and handles
        the sparse-sector case (fewer than 5 viable top-quartile peers) explicitly.

        Selection criteria (documented):
          sector_match:          Same top-level industry category as the prospect.
          employee_band:         0.25x to 4x the prospect's headcount.
          funding_minimum:       At least one funding round on record.
          top_quartile_threshold: AI maturity score >= 2 on the same 6-signal framework.
        """
        selection_criteria = {
            "sector_match": "Same top-level industry category as the prospect",
            "employee_band": "0.25x to 4x prospect headcount",
            "funding_minimum": "At least one funding round on record (excludes pre-revenue stubs)",
            "top_quartile_threshold": "AI maturity score >= 2 on the same 6-signal framework applied to the prospect",
            "max_returned": 10,
            "min_for_valid_analysis": 5,
        }

        prospect_record = self._find_catalog_record(crunchbase_id=crunchbase_id)
        if not prospect_record:
            log.error("prospect_record_missing_for_gap", crunchbase_id=crunchbase_id)
            return {
                "prospect_id": crunchbase_id,
                "sector": sector,
                "error": "Prospect record not available - competitor analysis cannot run",
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }

        prospect_record = self._normalize_company_record(prospect_record)
        prospect_employees = prospect_record.get("employee_count", 0) or 50
        sector_keywords = [kw.strip().lower() for kw in sector.replace("/", " ").split()]

        candidates = []
        for row in self._load_public_signal_catalog():
            if row.get("uuid") == crunchbase_id:
                continue
            row = self._normalize_company_record(row)
            categories = row.get("category_list", [])
            cat_string = " ".join(
                item.get("value", "") if isinstance(item, dict) else str(item)
                for item in categories
            ).lower()
            if not any(kw in cat_string for kw in sector_keywords):
                continue
            emp = row.get("employee_count", 0)
            if emp < prospect_employees * 0.25 or emp > prospect_employees * 4:
                continue
            if not row.get("funding_rounds", []):
                continue
            candidates.append(row)

        prospect_signals = await self._build_company_signal_set(prospect_record)
        if prospect_ai_score is None:
            prospect_ai_score = prospect_signals["ai_maturity"]["score"]

        scored = []
        for row in candidates[:30]:
            signals = await self._build_company_signal_set(row)
            maturity = signals["ai_maturity"]
            justification = [
                signal["evidence"]
                for signal in maturity.get("per_signal_breakdown", [])
                if signal.get("contribution") not in ("absent", None)
            ][:3]
            emp_count = row.get("employee_count", 0)
            hp = row.get("homepage_url") or ""
            scored.append({
                "name": row.get("name", "Unknown"),
                "domain": hp.replace("https://", "").replace("http://", "").rstrip("/"),
                "ai_maturity_score": maturity["score"],
                "ai_maturity_justification": justification,
                "ai_maturity_breakdown": maturity.get("per_signal_breakdown", []),
                "headcount_band": (
                    f"{max(1, emp_count // 10) * 10}_to_{(emp_count // 10 + 1) * 10}"
                    if emp_count else "unknown"
                ),
                "top_quartile": maturity["score"] >= 2,
                "sources_checked": [
                    breakdown.get("source_url", "")
                    for breakdown in maturity.get("per_signal_breakdown", [])
                    if breakdown.get("source_url")
                ][:4],
            })

        top_quartile = sorted(
            [candidate for candidate in scored if candidate["top_quartile"]],
            key=lambda item: item["ai_maturity_score"],
            reverse=True,
        )
        selected = top_quartile[:10]

        sparse_sector = len(selected) < 5
        sparse_sector_note = (
            f"Only {len(selected)} top-quartile peer(s) found in the '{sector}' sector matching the selection criteria. "
            f"Gap analysis proceeds with available peers; distribution-position confidence is reduced. "
            f"Consider broadening the sector definition or using adjacent-sector peers for a more robust comparison."
            if sparse_sector else None
        )
        if sparse_sector:
            log.warning("sparse_sector_detected", sector=sector, top_quartile_count=len(selected))

        sector_scores = [candidate["ai_maturity_score"] for candidate in scored] + [prospect_ai_score]
        rank = sum(1 for score in sector_scores if score <= prospect_ai_score)
        pct_rank = round(rank / len(sector_scores) * 100) if sector_scores else 50

        distribution_position = {
            "sector_sample_size": len(sector_scores),
            "top_quartile_count": len(top_quartile),
            "prospect_ai_maturity_score": prospect_ai_score,
            "prospect_percentile_rank": pct_rank,
            "description": (
                f"Prospect sits at approximately the {pct_rank}th percentile of the {len(sector_scores)}-company sector sample. "
                f"Top-quartile threshold is score >= 2 ({len(top_quartile)} of {len(sector_scores)} companies qualify)."
            ),
        }
        gap_findings = self._infer_gap_findings(prospect_ai_score, selected)

        return {
            "prospect_id": crunchbase_id,
            "sector": sector,
            "selection_criteria": selection_criteria,
            "competitors_analyzed": selected,
            "top_quartile_count": len(selected),
            "sparse_sector": sparse_sector,
            "sparse_sector_note": sparse_sector_note,
            "distribution_position": distribution_position,
            "gap_findings": gap_findings,
            "identified_gaps": gap_findings,
            "analysis_note": (
                "Top-quartile comparison from committed public-signal catalog using the same 6-signal "
                "AI maturity framework applied to the prospect"
            ),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
