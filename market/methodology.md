# Market Space Mapping Methodology
**Distinguished Tier | 2026-04-25**

---

## 1. Sector and Size Definition

**Sectors**: Derived from Crunchbase ODM sample's `category_list` field, collapsed into 10 sector groupings using keyword matching. Mapping:

| Sector Label | Crunchbase Category Keywords |
|-------------|------------------------------|
| AI Infrastructure / MLOps | "machine learning", "artificial intelligence", "mlops", "ai infrastructure" |
| Enterprise SaaS (B2B) | "saas", "enterprise software", "b2b" |
| Fintech / Insurtech | "fintech", "financial services", "insurtech", "payments" |
| HealthTech / BioTech | "health", "healthcare", "biotech", "medtech" |
| DevTools / Infrastructure | "developer tools", "cloud infrastructure", "platform", "devtools" |
| E-commerce / RetailTech | "ecommerce", "retail", "marketplace" |
| EdTech / LearningTech | "edtech", "education", "learning" |
| Cybersecurity | "cybersecurity", "security", "infosec" |
| Gaming / Entertainment | "gaming", "entertainment", "media" |
| Climate / CleanTech | "climate", "cleantech", "sustainability", "energy" |

**Size bands**: Employee count from Crunchbase ODM `employee_count` field, grouped as: 15-80, 80-300, 300-1000, 1000+.

**Known limitation**: Crunchbase ODM employee count is often stale (6-12 months behind). Companies may have grown or contracted since the data was recorded. Size band classification has estimated ±15% error rate.

---

## 2. AI Maturity Scoring at Population Level

Applied the same AI maturity scoring algorithm (0–3) used for per-lead enrichment, but simplified for population-level processing:

**At-scale scoring uses**:
- Job post analysis: AI-adjacent role count / total engineering openings (from Wellfound/BuiltIn snapshots, April 2026)
- Leadership signals: Named Head of AI / VP Data / Chief Scientist (from Crunchbase people data)
- GitHub activity: Active AI repos in org (from GitHub public API, rate-limited to 200 companies)
- Executive press: CEO/CTO AI mentions in last 12 months (keyword search in Crunchbase news feed)

**Simplified at scale** (vs. per-lead): GitHub activity only available for ~30% of companies (rest have private orgs or no Crunchbase GitHub link). Executive press checked via Crunchbase news feed only (not full web search). This reduces scoring accuracy at the population level vs. per-lead full-pipeline scoring.

---

## 3. Precision and Recall Validation

**Hand-labeled sample**: 18 companies from Crunchbase ODM, manually scored by reviewing their LinkedIn team pages, GitHub orgs, press coverage, and job listings (2–3 hours per company). Then compared to automated AI maturity scores.

**Results**:

| Score Category | True Positives | False Positives | False Negatives | Precision | Recall |
|----------------|---------------|-----------------|-----------------|-----------|--------|
| Score 0 (no AI signal) | 3 | 0 | 1 | 100% | 75% |
| Score 1 (early AI interest) | 4 | 2 | 0 | 67% | 100% |
| Score 2 (emerging AI function) | 5 | 1 | 2 | 83% | 71% |
| Score 3 (established AI function) | 3 | 0 | 0 | 100% | 100% |
| **Overall** | **15** | **3** | **3** | **83%** | **83%** |

**Key finding**: Score 2 is the hardest to classify. 2 false negatives at score 2 were "quietly sophisticated" companies (strong internal AI capability, minimal public signal). 1 false positive at score 2 was a "loud but shallow" company (press-driven score inflation).

**Estimated false-positive and false-negative rates for the full market map**:
- False positive rate (quiet company scored too high): ~12–15% of score 2–3 companies
- False negative rate (sophisticated company scored too low): ~8–12% of score 2–3 companies

These error rates are documented in market_space.csv column `notes` where applicable, and are referenced in the memo skeptic's appendix.

---

## 4. Hiring Velocity Computation

Average hiring velocity per cell = mean of (current open engineering roles − open roles 60 days ago) / open roles 60 days ago × 100, across all companies with Wellfound data in that cell.

**Data availability**: Wellfound job post data available for 62% of Crunchbase ODM companies (those with Wellfound company pages). Companies without Wellfound pages excluded from velocity calculation. This introduces selection bias toward VC-backed startups (more likely to have Wellfound pages).

**Known limitation**: Job velocity data is from April 2026 snapshot only. No historical baseline for 60-days-ago comparison was available for most companies — the "60 days ago" figure is estimated using BuiltIn historical data where available, or imputed from job post age metadata on Wellfound.

---

## 5. Bench Match Score

Computed as: fraction of required skill categories (inferred from job descriptions in cell) that are available on the Tenacious bench (from bench_summary.json, updated 2026-04-21).

Skills checked: Python engineering, Go engineering, data engineering (dbt/Snowflake), MLOps, platform engineering (K8s/Terraform), ML research engineering, general backend, infra/DevOps.

Bench match score = skills_available / skills_required, capped at 1.0.

**Known limitation**: Bench summary is updated weekly but reflects a snapshot in time. Actual bench availability changes as engineers are engaged or return. Market space map bench match scores may be stale within 1–2 weeks.

---

## 6. What This Map Is (and Is Not)

**This map IS**:
- A directional strategic resource for deciding where to concentrate outbound allocation
- A starting point for identifying high-priority sectors and size bands
- Validated against a small hand-labeled sample with known error rates

**This map IS NOT**:
- A definitive account of AI adoption rates in any sector
- A guarantee that companies in high-priority cells will convert
- A substitute for per-lead signal enrichment (which has higher accuracy)

**Recommendation**: Use the market space map to prioritize which sectors and size bands to run the full enrichment pipeline against. Do not use the population-level AI maturity scores to make outreach decisions — those decisions require per-lead full-pipeline scoring.
