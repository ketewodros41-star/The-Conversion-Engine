

## The Conversion Engine

An Automated Lead Generation and Conversion System for Tenacious Consulting
and Outsourcing

## Summary
The client for this challenge is Tenacious Consulting and Outsourcing — a real B2B firm
providing talent outsourcing and consulting services to technology-driven companies.
You are asked to design and build, in one week, an automated lead generation and
conversion system that the Tenacious executive team can evaluate for deployment. The
system finds new prospective clients from public data, qualifies them against a real intent
signal, runs a nurture sequence, and books discovery calls with a Tenacious delivery lead.
You will receive Tenacious marketing material, sample sales decks, anonymized email
templates, and the ideal-customer-profile definition as seed inputs. You will not receive
any real customer contact data, CRM exports, or names of live prospects. Every prospect
your system interacts with during the challenge week is a synthetic profile derived from
public Crunchbase, LinkedIn job-post, and layoffs.fyi data — not a real person. Real
deployment against Tenacious's live pipeline happens only after program staff and the
Tenacious executive team review and approve your final build.
The character of this challenge is specific: the system is not only a qualifier, it is a
researcher. The most successful submissions produce outputs a prospect would read with
interest rather than discomfort — a grounded view of their AI maturity, a comparison
against the top quartile of their sector, a specific gap worth a thirty-minute conversation.
Qualification is the filter; research is the value proposition.
The Client — Tenacious Consulting and Outsourcing
What Tenacious does
Tenacious Consulting and Outsourcing provides two primary services: managed talent
outsourcing (dedicated engineering and data teams operating under Tenacious
management but delivering to a client's product) and project-based consulting
engagements (time-boxed deliveries with defined scope — AI systems, data platforms,
specialized infrastructure). Clients are typically B2B technology companies in North
America and Europe, ranging from Series A startups scaling their first offshore team to
mid-market enterprises restructuring engineering cost. Typical engagement size: 3 to 12
engineers, 6 to 24 month duration.
Who Tenacious sells to
The ideal-customer-profile (ICP) definition, provided in the seed materials, identifies four
primary segments.


## Segment

## Description

Why they buy

## Recently-funded Series
A/B startups
Companies that closed a $5–30M
round in the last 6 months.
Typically 15–80 people. Hiring
velocity outstripping recruiting
capacity.
Need to scale engineering output
faster than in-house hiring can
support. Budget is fresh and runway
is the clock.
Mid-market platforms
restructuring cost
Public or late-stage companies
(200–2,000 people) under pressure
to cut burn without cutting
output. Often post-layoff or
post-restructure.
Replace higher-cost roles with
offshore equivalents; keep delivery
capacity; quiet signal of operational
discipline to the board.
## Engineering-leadership
transitions
Companies with a new CTO or VP
Engineering appointed in the last
90 days.
New leaders routinely reassess
vendor contracts and offshore mix
in their first 6 months. This is a
narrow but high-conversion
window.
Specialized capability
gaps
Companies attempting a specific
build — ML platform migration,
agentic systems, data contracts —
where in-house skills do not
match the need.
Project-based consulting, not
outsourcing. Higher margin, shorter
commitment, portfolio value.
Current pain (from Tenacious executive interviews)
The Tenacious CEO and CFO describe three linked problems. Outbound prospecting is
manual: a partner or senior engineer identifies promising companies in an ad-hoc way,
often through personal network or LinkedIn browsing, with no systematic coverage of the
market. Qualification is inconsistent: two prospects with identical firmographics get very
different first messages because the person reaching out applies intuition rather than a
repeatable playbook. Follow-up is slow: once a prospect responds, the person who
initiated the conversation must personally handle the thread, which queues behind
delivery work and loses momentum.
The revenue consequence is a long tail of conversations that stalled not because the
prospect said no but because Tenacious did not keep up. The Tenacious CFO estimates
this at 30–40% of qualified conversations stalling in the first two weeks.

## What You Receive From Tenacious
Seed materials are delivered to you via a private repo on Day 0. They are the raw inputs
your system will use. They do not include any identifying customer data.


## Seed Material

## Purpose

## Constraint

ICP definition
## (markdown)
Defines the four segments above with
qualifying and disqualifying filters.
May be adapted by the agent,
but the segment names are
fixed for grading.
Sales deck
## (anonymized)
The master deck used on discovery
calls. Source of truth for positioning,
services, pricing bands.
Do not reference client logos or
case-study names beyond what
is in the deck.
Case studies (redacted)
Three case studies with client names
replaced by sector + size descriptors.
You may quote outcomes but
may not fabricate additional
case studies.
Sample outbound
email sequences
Three email sequences (cold, warm,
re-engagement) in the Tenacious
voice.
Agents may rewrite these but
must preserve the tone markers
defined in style_guide.md.
Sample discovery call
transcripts (synthetic)
Five transcripts synthesized from the
Tenacious sales team's style — not real
calls.
Use for tone,
objection-handling patterns,
and pricing language.
Pricing sheet
Public-tier pricing bands per segment
and engagement type.
Agents may quote these;
deeper pricing must route to a
human.
Delivery bench
summary
Counts of available engineers per stack
(Python, Go, data, ML, infra).
Updated at the start of the
week; the agent should
reference actual capacity not
hallucinate it.


Sales Jargon for Talent Outsourcing
Core concepts
- SDR work (outbound). In this context, finding net-new companies that match ICP
and making first contact. Volume target in Tenacious's current practice is ~60
thoughtful outbound touches per week per person.
- Bench. Engineers currently employed by Tenacious who are between engagements
and available to staff new work. Bench utilization is a primary operating metric — low
utilization means lost margin, high utilization means missed opportunities.
- ICP match. A binary plus-or-minus on whether a prospect fits one of the four
segments. Agents must report confidence in the match, not assert certainty.
- Discovery call. First scheduled conversation between prospect and a Tenacious
delivery lead. The agent's final objective is to book this call with a clear context brief
attached.
- Bench-to-brief match. A check that the prospect's stated or inferred need (for
example, Python data engineers) matches current bench availability. The agent must
never commit to capacity that the bench summary does not show.
What replaces CFPB complaints — the hiring signal brief
In the compliance-software version of this challenge, the agent grounded the
conversation in CFPB complaint data. For Tenacious, there is no regulator database.
Instead, the agent grounds the conversation in a hiring signal brief — a combination of
public signals that make the prospect's buying window concrete and verifiable.

## Signal

## Source

What it tells the agent

Funding event
Crunchbase ODM sample;
press releases
Series A/B in last 180 days means fresh budget,
a plausible buying window, urgency from
runway clock.
Job-post velocity
BuiltIn, Wellfound, LinkedIn
public job feeds (scraped
via Playwright)
Open engineering roles tripled in 60 days
means hiring velocity outstripping in-house
recruiting.
## Layoffs
layoffs.fyi (CC-BY, structured
## CSV)
Layoff in last 120 days means cost pressure;
possible candidate for Segment 2
(restructuring) pitch, not Segment 1.
## Leadership
change
Crunchbase + press releases
New CTO/VP Eng in last 90 days means a
narrow vendor-reassessment window —
Segment 3 pitch.
Tech stack
BuiltWith, Wappalyzer
public data
Matches prospect stack to Tenacious bench.
Bench-to-brief match is gated on this.
AI maturity
Job posts, team pages,
GitHub org, press and blog
signal, exec talks
A 0–3 score of how ready the prospect is to
engage on AI work. Gates Segment 4

## Signal

## Source

What it tells the agent

(capability gap) pitches and shifts the pitch
language for Segments 1 and 2.
AI maturity scoring in more detail
AI maturity is a public-signal estimate of how seriously a prospect is already engaging
with AI. It is a sibling of the other hiring signals, not a separate category. The metric is a
0–3 integer with explicit per-signal justification so the agent can reference it without
over-claiming.

Signal input

What to look for

## Weight

AI-adjacent open roles
ML engineer, applied scientist, LLM engineer, AI product
manager, data platform engineer. Count as a fraction of
total engineering openings.
## High
Named AI/ML
leadership
Head of AI, VP Data, Chief Scientist, or equivalent on the
public team page or LinkedIn.
## High
Public GitHub org
activity
Recent commits on repos involving model training,
inference, or AI tooling. Absence is not proof of absence —
many companies keep AI work private.
## Medium
Executive commentary
CEO or CTO posts, keynotes, or interviews in the last 12
months that name AI as strategic.
## Medium
Modern data/ML stack
BuiltWith or Wappalyzer signal for tools like dbt,
Snowflake, Databricks, Weights and Biases, Ray, vLLM.
## Low
## Strategic
communications
Annual reports, fundraising press, or investor letters that
position AI as a company priority.
## Low

Score 0 means no public signal of AI engagement — the prospect is either intentionally
silent or simply absent. Score 3 means an active AI function with recent executive
commitment and multiple open roles. Scores 1 and 2 are the interesting middle where
most targets sit.
How AI maturity changes the pitch
The score gates one segment and shifts the language in two others. Segment 4
(specialized capability gaps — ML platform migration, agentic systems) is only pitched at
readiness 2 or above; reaching out to a score-0 prospect with a Segment 4 pitch wastes
the contact and damages the brand. Segment 1 (recently funded) is pitched at any score,
but the language shifts: at high readiness, ‘scale your AI team faster than in-house hiring
can support’; at low readiness, ‘stand up your first AI function with a dedicated squad’.
Segment 2 (mid-market restructuring) behaves similarly. Segment 3 (leadership
transition) is unaffected because the new leader's own AI stance is the variable that
matters, not the prior state of the company.

The agent must carry confidence with the score. A readiness of 2 inferred from weak
signals (one or two medium-weight inputs) is phrased differently from a readiness of 2
backed by multiple high-weight inputs. Low confidence paired with a high score must
trigger softer language: ask rather than assert.
How the agent uses the brief
The hiring signal brief transforms a cold outreach from ‘you might need offshore
engineering capacity’ to ‘you closed a $14M Series B in February and your open
Python-engineering roles tripled since then — the typical bottleneck for teams in that
state is recruiting capacity, not budget’. The difference is the second message is verifiable
against the prospect's own public record and is therefore hard to object to.
The same honesty constraint from the compliance version applies. The agent refuses to
make claims it cannot ground in the brief. If the job-post signal is weak (fewer than five
open roles), the agent does not claim ‘you are scaling aggressively’ — it asks rather than
asserts. Over-claiming damages Tenacious's reputation with a potential client more than
silence would.
Baseline numbers
Public references plus Tenacious-internal numbers provided for this challenge.
Over-claiming against these is penalized. Under-claiming without explanation is
penalized.

## Metric

## Reference

## Source

B2B outbound cold-email reply rate
## (baseline)
## 1–3%
LeadIQ 2026 / Apollo
benchmarks
Signal-grounded outbound reply
rate (top-quartile)
7–12% Clay, Smartlead case studies
## Discovery-call-to-proposal
conversion
## 35–50%
Tenacious internal, last 4
quarters
Proposal-to-close conversion 25–40%
Tenacious internal, last 4
quarters
Average engagement ACV (talent
outsourcing)
## $240–$720K
Tenacious internal, weighted
by segment
Average engagement ACV (project
consulting)
## $80–$300K
Tenacious internal, last 8
deals
Stalled-thread rate, current manual
process
30–40% Tenacious executive interview
Voice agent conversational pass@1
ceiling
~42% τ²-Bench retail
τ²-Bench leaderboard, Feb
## 2026
## The Data

Data Source 1 — Crunchbase ODM Sample
What it is

1,001 real Crunchbase company records extracted under Apache 2.0
license. Firmographics, funding, founders, industry, location.
Where to get it
github.com/luminati-io/Crunchbase-dataset-samples
Your use

Primary firmographic source for every prospect your system reaches out
to. Every lead object in HubSpot must reference a Crunchbase record.

Data Source 2 — layoffs.fyi
What it is

Structured CC-BY dataset of tech-industry layoffs, updated weekly.
Company name, date, headcount, percentage cut, source.
Where to get it
layoffs.fyi (downloadable CSV) or the HuggingFace mirror
Your use

Layoff signal input to the hiring signal brief. Combined with funding and
job-post data to classify the prospect into one of the four ICP segments.

## Data Source 3 — Public Job Posts
What it is

Public job-post listings from BuiltIn, Wellfound, and LinkedIn company
pages. Collected via Playwright for the challenge week; not a live feed.
## Restriction

Use only public pages. Do not log in. Do not bypass captchas. Respect
robots.txt. A sample frozen dataset from early April 2026 is provided in
the seed repo — you may use either that snapshot or a small live crawl of
no more than 200 companies during the challenge week.
Your use

Job-post velocity signal. Track change over 60 days to produce the
velocity number used in the brief.

Data Source 4 — τ²-Bench
What it is

A dual-control conversational agent benchmark from Sierra Research.
Published reference for B2B conversational agent performance.
Where to get it
github.com/sierra-research/tau2-bench
Your use

Ground-truth conversation benchmark. You reproduce the baseline,
design adversarial probes, and implement a mechanism measured on a
sealed held-out slice. The τ²-Bench retail domain is the closest public
analog to B2B qualification conversation; the telecom domain supplies
useful secondary probes.
## Data Handling Policy

This challenge involves a real client. The policy below governs what you may do with what
data. Violations are grounds for removal from the program.
## Rules
- No real Tenacious customer data leaves Tenacious. You do not receive CRM exports,
email threads with real prospects, real phone numbers, or real names of live deals.
- Every prospect your system interacts with during the challenge week is synthetic.
Synthetic prospects are generated from public Crunchbase firmographics combined
with fictitious contact details. The program-operated SMS rig routes all outbound
messages to a staff-controlled sink, not to real people.
- Seed materials (sales deck, case studies, pricing sheet) are shared under a limited
license for the challenge week. You may not redistribute them. At the end of the
week, all copies must be deleted from any personal infrastructure; code may be kept
in your program repo.
- If your code could plausibly be run against real Tenacious prospects after the week,
the README must document that explicitly and must include a kill-switch: a
configuration flag that, when unset, routes all outbound to the staff sink. Default
must be unset.
- Any outputs of your system that include Tenacious-branded content (emails, call
scripts, pricing) must be marked 'draft' in metadata. The Tenacious executive team
reserves the right to redact any such content from your final memo.

## The Production Stack
Same principles as the Ethiopia-friendly version of this challenge: no credit-card or
US-number barriers, SMS primary, voice as a bonus tier, cost envelope under $20 per
trainee for the week.

## Layer

## Primary Choice

## Notes

## Email (primary
channel for
## Tenacious)
Resend (free tier, 3,000
emails/month) or MailerSend
free tier
Both offer free tiers without a credit card.
Tenacious prospects are reached by email
first; SMS is secondary for fast
re-engagement only.
SMS (secondary
channel)
Africa's Talking sandbox
Free; two-way SMS virtual short codes;
routed to a staff sink during the challenge
week.
## Voice (bonus) Tenacious Shared Voice Rig
Program-operated rig. Registered
webhook + keyword prefix per trainee.
CRM HubSpot Developer Sandbox Free; MCP server; 100 API calls per 10s.

## Layer

## Primary Choice

## Notes

Calendar Cal.com self-hosted
Docker Compose; Tenacious team
calendars mocked by program-provided
sample calendars.
Backbone LLM (dev
tier)
OpenRouter with
Qwen3-Next-80B-A3B or
DeepSeek V3.2
Probe and ablation development. Target
under $4 Days 1–4.
Backbone LLM (eval
tier)
Claude Sonnet 4.6 or GPT-5
class
Sealed held-out scoring only. Target under
## $12 Days 5–7.
Enrichment / signal
collection
Playwright + FastAPI wrapper
Job-post scraping + layoffs.fyi parsing +
Crunchbase ODM lookup.
Observability Langfuse (cloud free tier) Per-trace cost attribution.
Evaluation harness τ²-Bench Non-substitutable benchmark anchor.
Why email is primary for Tenacious
Unlike the compliance-software case, Tenacious's prospects are founders, CTOs, and VPs
Engineering who live in email, LinkedIn, and occasionally Slack. Cold SMS to this segment
is unusual and frequently perceived as intrusive. The primary conversation channel is
email; SMS is reserved for warm leads who have replied once and want fast coordination
around scheduling. Voice is the final channel: a discovery call, booked by the agent,
delivered by a human Tenacious delivery lead.
This is a deliberate scope choice. A trainee who rebuilds the compliance version's
voice-heavy architecture here will find their prospects do not respond to voice cold
outreach. The challenge rewards matching channel to segment.


## Day 0 — Pre-flight Checklist
Complete before Day 1. Roughly four hours. A readiness review on Day 1 morning confirms
each item.

## Item

What done looks like

Resend or MailerSend account
provisioned
Free-tier account live. Sent one test email to your own address
and received it. Webhook URL registered for reply handling.
Africa's Talking sandbox
Account created. Virtual short code registered. One test SMS
routed to your webhook handler.
HubSpot Developer Sandbox
App created. MCP server installed. One test contact created via
## API.
Cal.com running locally
docker compose up succeeds. One test booking flows
end-to-end.
Langfuse cloud Project created. One test trace visible.
τ²-Bench cloned Retail domain runs against pinned dev-tier model on three tasks.
Seed repo forked
Tenacious ICP, sales deck, email sequences, pricing sheet, bench
summary all present. style_guide.md reviewed.
Signal pipeline skeleton
Playwright installs. A 10-line script fetches one public job listing
and saves it as JSON.
Data-handling policy signed Signed digital acknowledgement filed with program staff.


The Five-Act Loop
Act I — Baseline and Ground Truth
Goal: Reproduce a τ²-Bench retail baseline within pinned model and settings. Establish
your own ground-truth baseline before touching any Tenacious-specific code.
- Clone τ²-Bench, run the retail domain with the pinned dev-tier model.
- Wrap the harness so every run writes trace_log.jsonl to Langfuse and updates
score_log.json.
- Accept the program-delivered sealed held-out partition (20 tasks). Work against the
30-task dev slice only.
- 5-trial pass@1 on the dev slice. Record mean, 95% CI, cost per run, p50/p95 latency.
## Deliverable
- score_log.json, trace_log.jsonl, baseline.md (max 400 words).
Act II — Production Stack Assembly
Goal: Stand up the full email plus SMS plus CRM plus calendar plus signal-enrichment
loop. End-to-end: one synthetic prospect receives an email, replies, gets qualified, books a
discovery call, appears correctly in HubSpot and Cal.com.
Required integrations
- Email out via Resend / MailerSend, reply webhook to your backend.
- Africa's Talking SMS fallback for warm leads who prefer SMS for scheduling.
- HubSpot MCP for every conversation event.
- Cal.com booking flow integrated into the email and SMS handlers.
Signal enrichment pipeline
Runs before the agent composes the first outreach:
- Pull firmographics from Crunchbase ODM sample for the target company.
- Fetch funding events in the last 180 days (from Crunchbase).
- Scrape job posts from the company's public BuiltIn / Wellfound / careers page
(respecting robots.txt).
- Check layoffs.fyi for any event in the last 120 days.
- Check for leadership changes (new CTO / VP Engineering) in press releases or
## Crunchbase.
- Score AI maturity (0–3) from the signal inputs defined in the hiring signal brief
section, with per-input justification.
- Produce competitor_gap_brief.json: identify 5–10 top-quartile competitors in the
prospect's sector, apply the same AI-maturity scoring to each, compute the
prospect's position in the sector's distribution, and extract 2–3 specific practices the
top quartile shows public signal for that the prospect does not.
- Merge into hiring_signal_brief.json and competitor_gap_brief.json with per-signal
confidence scores.

Why the competitor gap brief matters
The competitor gap brief converts outbound from a vendor pitch into a research finding.
The value proposition the agent carries into the first message shifts from ‘Tenacious offers
X’ to ‘three companies in your sector at your stage are doing X and you are not — here is
what the difference looks like’. This is a stronger hook and a harder one to execute well.
The grading in Act III reflects both: credit for producing useful briefs, penalty for tone
failures when the brief is delivered poorly.
## Deliverable
- One complete email + SMS + calendar thread for a synthetic prospect, end-to-end.
- HubSpot screenshot with all fields populated and enrichment timestamps present.
- Cal.com booking screenshot.
- p50/p95 latency across at least 20 synthetic prospect interactions.
Act III — Adversarial Probing
Goal: 30+ adversarial probes classified by business cost. Identify the highest-ROI failure
mode to attack in Act IV.
Probe categories for Tenacious
- ICP misclassification — does the agent put a post-layoff company in Segment 1
(freshly funded) by accident? What is the cost of the wrong pitch?
- Signal over-claiming — does the agent assert ‘aggressive hiring’ when the job-post
signal is weak? Grounded-honesty is a Tenacious brand constraint.
- Bench over-commitment — does the agent ever promise capacity the bench
summary does not show?
- Tone drift — does the agent's language drift from the Tenacious style guide after
three or four turns of back-and-forth?
- Multi-thread leakage — if the same agent talks to two prospects at the same
company (co-founder and VP Eng), do messages leak context across threads?
- Cost pathology — any prompt that causes runaway token usage.
- Dual-control coordination — τ²-Bench's central failure mode: waiting for the user's
action versus proceeding.
- Scheduling edge cases — does the agent handle time-zone confusion correctly?
Tenacious serves EU, US, and East Africa; the prospect pool spans all three.
- Signal reliability — for each hiring signal and AI-maturity score, what public evidence
supports it, and what is the known false-positive rate against a small hand-labeled
sample? Does the agent's confidence language match the evidence weight?
- Gap over-claiming — does the agent ever assert a competitor gap unsupported by
the brief? Does the framing of a real gap ever sound condescending to a CTO who is
already painfully aware? Test with defensive-reply scripts and measure tone drift
under pressure.
## Deliverable
- probe_library.md with 30+ structured entries .

- failure_taxonomy.md grouping probes by category.
- target_failure_mode.md naming the highest-ROI failure, with explicit business-cost
derivation in Tenacious terms.
Act IV — Mechanism Design
Goal: Design an original mechanism that addresses your target failure mode. Beat your
Day-1 baseline on the sealed held-out slice with 95% CI separation. Honestly report against
the automated-optimization baseline (GEPA or AutoAgent).
## Deltas
- Delta A. your_method − your_day1 baseline. Must be positive with 95% CI separation.
- Delta B. your_method − automated-optimization baseline on the same compute
budget. Failing Delta B does not fail the week; unexplained underperformance does.
- Delta C. your_method − published τ²-Bench reference. Informational only.
Mechanism directions worth considering
- Signal-confidence-aware phrasing. Your hiring signal brief carries per-signal
confidence. Let the agent's phrasing shift automatically when confidence is low.
- Bench-gated commitment policy. A hard constraint that the agent cannot commit
to capacity the bench summary does not show, with explicit handoff to a human
when the prospect asks for specific staffing.
- ICP classifier with abstention. A lightweight classifier that scores segment
confidence; if confidence is below threshold, the agent sends a generic exploratory
email rather than a segment-specific pitch.
- Tone-preservation check. A second model call that scores whether the agent's latest
draft drifts from the Tenacious style guide, with regeneration if score falls below
threshold. Cost the extra call.
- Multi-channel handoff policy. Explicit rules for when to switch a thread from email to
SMS to voice, measured against engagement outcomes.
## Deliverable
- method.md, ablation_results.json, held_out_traces.jsonl.
- Statistical test showing Delta A positive with p < 0.05.
## Act V — The Memo
Goal: Two-page decision memo addressed to the Tenacious CEO and CFO. Every number
traces to a trace file or a published source. The memo is the deliverable that determines
whether this system is ever run against real Tenacious prospects.
## Page 1 — The Decision
- Three-sentence executive summary.
- Baseline performance on τ²-Bench retail with 95% CIs.
- Cost per qualified lead, derived from rig usage + LLM spend + trace count.

- Stalled-thread rate delta. Current Tenacious manual process (30–40%) vs. your system
(measured from your traces). If your number is lower, show the math.
- Competitive-gap outbound performance. The fraction of outbound that led with a
research finding (AI maturity score + top-quartile gap) vs. a generic Tenacious pitch,
and the reply-rate delta between them. Source: traces tagged by outbound variant.
- Annualized dollar impact at three adoption scenarios: one segment only, two
segments, all four. Each scenario includes expected deal volume, conversion rates,
and ACV.
- Pilot scope recommendation: one segment, a specific lead volume, a specific weekly
budget, one measurable success criterion Tenacious can track after 30 days.
## Page 2 — The Skeptic's Appendix
- Four failure modes τ²-Bench does not capture but would show up in the Tenacious
deployment. Be specific — ‘the agent will say something the founder takes offense
to’ is vague; ‘the agent uses offshore language that triggers in-house hiring
managers’ is specific.
- Public-signal lossiness. Name the known false-positive and false-negative modes of
your AI-maturity scoring. What does a quietly-sophisticated-but-silent company look
like in your system? What does a loud-but-shallow one look like? For each, what does
the agent do wrong and what is the business impact?
- Gap-analysis risks. Under what conditions is a top-quartile practice a bad benchmark
— for example, a deliberate choice by the prospect not to follow the sector
consensus, or a capability that genuinely does not matter in their sub-niche? One
paragraph per real risk, with an example from your data.
- The brand-reputation comparison. If your agent sends 1,000 emails with the
signal-grounded approach and 5% have factually wrong signal data, is the brand
damage worth the 7–12% reply rate? Show the unit economics with an explicit
assumption about the reputation cost of a wrong-signal email.
- One honest failure. A probe from your Day-4 library that you did not resolve, and the
impact if deployed anyway.
- The kill-switch clause. Under what measurable condition should the Tenacious CEO
pause this system? Specify the trigger metric and threshold.
## Deliverable
- memo.pdf — 2 pages.
- evidence_graph.json.
- README.md written for the engineer who would inherit this after you.


## Market Space Mapping
The five-act deliverables are the floor. For distinguished-tier credit, one additional
deliverable is available: a market-space map that takes the per-lead capability built in Acts
II and IV and applies it at the population level.
The work
Take the full Crunchbase ODM sample, segment it by sector and company size, apply
AI-maturity scoring to every company, and cluster the results into subsector-by-readiness
cells. The output is a table that tells the Tenacious executive team which cells contain the
most oxygen for outbound — funded companies that are hiring, that show meaningful AI
openness, and whose likely capability gaps match the Tenacious delivery bench. The
finding is strategic, not tactical. It answers where to point the system, not just how the
system performs on an arbitrary input.
## Outputs
- market_space.csv: one row per (sector, company-size band, AI-readiness band) cell,
with cell population, average funding in the last 12 months, average hiring velocity,
and bench-match score against the Tenacious capability summary.
- top_cells.md: the three to five cells ranked highest on the combined score, with a
one-paragraph profile of each and a specific recommendation for outbound
allocation.
- methodology.md: how sectors were defined, how scoring was validated against a
small hand-labeled sample, and what false positives and negatives are known to
exist in the map.
Why this is a stretch and not a required deliverable
The underlying capability — scoring AI maturity from public signal — is already built for
the per-lead use case in Acts II and IV. Extending it to the population is leverage, not new
engineering. But doing it honestly requires validation effort the challenge week will not
naturally provide: you must hand-label a sample of companies, compute precision and
recall of your scoring, and publish the error bars. A superficial market map is worse than
none because it misdirects strategy with false confidence. Trainees who attempt this must
budget Day 6 carefully and must not let the stretch compromise the core five-act
deliverables.

What distinguished-tier credit means here
A market-space map that would change how Tenacious allocates outbound effort earns a
distinguished rating on the Cost-Quality Pareto observable and an originality credit on Probe
## Originality.



## Deliverables
Interim Submission: Wednesday April 22, 21:00 UTC
Submit: GitHub repo + PDF report (public Google Drive link)
This deadline covers Acts I and II: the τ²-Bench baseline and the full production stack
running end-to-end.
GitHub Repo Requirements
● README.md at root with architecture diagram, setup instructions, and
requirements
● agent/ directory containing all agent source files, email handler (Resend or
MailerSend integration), SMS handler (Africa's Talking for warm-lead scheduling),
HubSpot MCP integration, Cal.com booking flow, enrichment pipeline, and
requirements.txt
● eval/ directory containing τ²-Bench harness source, score_log.json with at least
your Act I dev-tier baseline and reproduction check both with 95% CI, and
trace_log.jsonl with full τ²-Bench trajectories across all dev trials
● baseline.md covering what you reproduced, your confidence interval, cost per run,
and any unexpected behavior. Max 400 words.
PDF Report Requirements
● Architecture overview and key design decisions
● Production stack status: Resend or MailerSend (email, primary channel), Africa's
Talking (SMS, secondary for warm-lead scheduling), HubSpot Developer Sandbox,
Cal.com, and Langfuse all verified running
● Enrichment pipeline status: Crunchbase ODM firmographics, job-post velocity
scraping, layoffs.fyi integration, leadership-change detection, and AI maturity
scoring (0 to 3) all producing output
● Competitor gap brief status: top-quartile comparison pipeline generating
competitor_gap_brief.json for at least one test prospect
● τ²-Bench baseline score and methodology
● p50/p95 latency numbers from at least 20 real email and SMS interactions pulled
from trace log
● What is working, what is not, and what the plan is for remaining days

Final Submission: Saturday April 25, 21:00 UTC
Submit: GitHub repo + PDF report + Demo Video (all public, no login required)
GitHub Repo (adds to Wednesday's)
probes/ directory
● probe_library.md with 30+ structured probe entries covering: ICP misclassification,
hiring-signal over-claiming, bench over-commitment, tone drift from Tenacious
style guide, multi-thread leakage, cost pathology, dual-control coordination,

scheduling edge cases (EU/US/East Africa time zones), signal reliability with
false-positive rates, and gap over-claiming from the competitor brief
● failure_taxonomy.md grouping probes by category with observed trigger rates
● target_failure_mode.md naming the single highest-ROI failure mode with explicit
business-cost derivation in Tenacious terms (referencing ACV, stalled-thread rates,
and brand-reputation impact)
Method and evaluation files
● method.md documenting the mechanism, design rationale, hyperparameters,
and three ablation variants tested, plus a statistical test confirming Delta A is
positive with p < 0.05
● ablation_results.json with pass@1, 95% CI, cost-per-task, and p95 latency for your
method, your Day 1 baseline, and the automated-optimization baseline, all on the
sealed held-out slice
● held_out_traces.jsonl with raw traces from each of the three conditions
● evidence_graph.json mapping every numeric claim in the memo to its source
trace ID or invoice line item
PDF Report (memo.pdf, exactly 2 pages, no more no less)
## Page 1: The Decision
● Executive summary in three sentences: what was built, headline number,
recommendation
● τ²-Bench pass@1 results: published reference, Day 1 baseline, and your method, all
with 95% CIs, sourced from held_out_traces.jsonl
● Cost per qualified lead derived from rig usage, LLM spend, and trace count,
sourced from invoice_summary.json and trace_log.jsonl
● Speed-to-lead delta: current Tenacious manual process (stalled-thread rate of 30 to
40%) vs. your system's measured stalled-thread rate from traces
● Competitive-gap outbound performance: fraction of outbound that led with a
research finding (AI maturity score + top-quartile competitor gap) vs. a generic
Tenacious pitch, and the reply-rate delta between them, sourced from traces
tagged by outbound variant
● Annualized dollar impact at three adoption scenarios (one segment only, two
segments, all four segments), each reproducible from trace files and published
Tenacious conversion rates and ACV ranges
● Pilot scope recommendation: one segment, one lead volume, one dollar budget,
one measurable success criterion Tenacious can track after 30 days
## Page 2: The Skeptic's Appendix
● Four failure modes τ²-Bench does not capture but would appear in a real Tenacious
deployment, each with what it is, why the benchmark misses it, what would need
to be added to catch it, and what that would cost. Failures must be
Tenacious-specific (e.g., offshore-perception objections, bench mismatch,
brand-reputation risk from wrong hiring signals).
● Public-signal lossiness: name the known false-positive and false-negative modes of
AI maturity scoring. What does a quietly sophisticated but publicly silent company
look like in your system? What does a loud but shallow one look like? For each,
what does the agent do wrong and what is the business impact?
● Gap-analysis risks: under what conditions is a top-quartile practice a bad
benchmark (e.g., a deliberate strategic choice by the prospect, or a capability
irrelevant to their sub-niche)? One paragraph per real risk, with an example from
your data.

● Brand-reputation comparison: if the agent sends 1,000 signal-grounded emails
and 5% contain factually wrong signal data, is the brand damage worth the 7 to
12% reply rate? Show the unit economics with an explicit assumption about the
reputation cost of a wrong-signal email.
● One honest unresolved failure from the probe library with business impact
assessment
● Kill-switch clause: specific trigger metric, threshold, and rollback condition
Demo Video (max 8 minutes, no login required)
● Live email conversation end-to-end showing a synthetic prospect receiving a
signal-grounded outreach email, replying, getting qualified through the hiring
signal brief (Crunchbase funding, job-post velocity, layoffs.fyi, leadership changes,
AI maturity score), and having a discovery call booked via Cal.com
● Show the hiring signal brief and competitor gap brief being generated for the
prospect, with per-signal confidence scores visible
● Show HubSpot contact record populating in real time with all fields non-null and
enrichment timestamp current
● Show an SMS scheduling interaction for a warm lead who has already replied by
email (demonstrating email-to-SMS channel handoff)
● Show the agent correctly refusing to over-claim when a hiring signal is weak (e.g.,
not asserting "aggressive hiring" when fewer than five open roles exist)
● Show the agent correctly handling a prospect whose signals place them in a
different ICP segment than a naive classification would suggest (e.g., a post-layoff
company that also recently raised funding)
● Show τ²-Bench harness producing a score with query trace visible
● Brief walkthrough of probe library and how at least one probe led to a concrete fix
● Bonus: one real voice call end-to-end through the Shared Voice Rig if completed

Note on channel priority: Email is the primary outreach channel for Tenacious
prospects (founders, CTOs, VPs Engineering). SMS is secondary, reserved for warm
leads who have replied by email and prefer fast coordination for scheduling. Voice is
the final channel: a discovery call, booked by the agent, delivered by a human
Tenacious delivery lead. Deliverables should reflect this channel hierarchy
throughout.









Evidence-Graph Grading

## Observable

Tenacious-specific note

Reproduction fidelity Graded against pinned τ²-Bench retail reproduction.
Probe originality
Probes must be specifically diagnostic of Tenacious failure modes, not
generic B2B ones. A probe that only makes sense for talent
outsourcing earns higher originality credit.
Mechanism attribution Automated statistical check on Delta A.
## Cost-quality Pareto
Per qualified lead, not per message. If cost per lead exceeds $8
without justification, penalty applies. Tenacious's target is under $5.
Evidence-graph integrity
Every claim in the memo must map to a trace file, a
Tenacious-provided number (bench summary, historical conversion
rates), or a public source. Fabricated Tenacious numbers are a
disqualifying violation, separate from the standard penalty.
Skeptic's appendix quality
Must address Tenacious-specific risks: brand reputation, bench
mismatch, offshore-perception objections. Generic risks penalized.

Beyond grading — the real prize
The best submission from this week becomes the starting point for a Tenacious pilot. The
trainee (or small team) whose system is selected gets the opportunity to run the pilot against
real Tenacious prospects, with program-staff oversight, over the four weeks after the challenge
closes. That is the real grade — whether your work is trustworthy enough that the Tenacious
CEO is willing to point it at live revenue.


Find the lead. Ground the conversation. Respect the brand. Ship it.
