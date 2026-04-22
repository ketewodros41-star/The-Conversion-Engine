

## The Conversion Engine

A Production-Grade SMS and CRM Agent for B2B Sales Development  ·  Acme
ComplianceOS Edition

## Summary
You are deployed to a hypothetical mid-market B2B SaaS company selling compliance
software to financial institutions. Inbound leads arrive from the website, from a
Crunchbase-seeded outbound campaign, and from a partner referral stream. The
company loses roughly 60% of inbound leads to response-time failures and qualification
errors. Your job, in one week, is to build the agent that handles the first 72 hours of every
new lead — running an SMS nurture sequence, qualifying the lead against real
Crunchbase firmographic data, checking the prospect's regulatory exposure against CFPB
complaint history, booking a discovery call into a real calendar, and writing every
interaction back into HubSpot as a structured record.
Voice is the bonus tier. Trainees who complete the SMS and CRM core by Day 5 may add a
voice channel on Days 6–7. The baseline is what exists today in the market. The
benchmark is τ²-Bench. Every number in your final memo must resolve to a trace file a
reviewer can open and read.
## The Business Context
## The Hypothetical Client
Acme ComplianceOS is a fictitious but realistic mid-market SaaS company. They sell a
compliance automation platform to community banks, credit unions, and regional
financial services firms in the United States. Average contract value is $60,000 annually.
Sales cycle averages 90 days. The SDR team of six handles roughly 120 qualified inbound
leads per month and an outbound outreach volume of around 400 accounts per month.
Their current stack: HubSpot CRM, a marketing automation layer pushing emails, a shared
inbox for inbound, a Google Voice number that rings whichever SDR is available, and a
manual process for pulling Crunchbase firmographic data into the CRM when an SDR
happens to have time. Their current pain is what every mid-market B2B company's
current pain looks like in April 2026: slow response times on inbound, inconsistent
qualification, and a long tail of leads that go cold before anyone touches them.
Baseline numbers — public references
These numbers are taken from public industry research and serve as the reference
distribution for your final memo. Over-claiming against these is penalized. Under-claiming
without explanation is penalized.


## Metric

## Industry Reference

## Source

Inbound lead response time (human
baseline)
42 minutes median; 17 hours
average
HBR / Lead Response
## Management Study
## Response-within-5-minutes
conversion lift
21× more likely to qualify
InsideSales.com / MIT
## Lead Response Study
Speed-to-lead human labor cost
~$42 per SDR-hour loaded cost
(US mid-market)
Bureau of Labor
Statistics / RepVue 2026
AI customer-service ROI (published
range)
$3.50 return per $1; leaders hit
## 8×
Deloitte State of AI 2026
B2B conversational agent pass@1
ceiling
~42% on τ²-Bench retail; ~30%
on telecom
τ²-Bench leaderboard,
## Feb 2026
HubSpot Breeze outcome-based
reference pricing
$0.50 per resolved conversation;
$1 per qualified lead
HubSpot announcement
## April 14, 2026
## The User Personas
Three users interact with your system. Each has different tolerance levels and different
success criteria.

## Persona

## Channel

What success looks like

Inbound buyer (Michelle,
VP Compliance at an
$800M credit union)
Submits a website form after
seeing an ad. Gets an SMS
reply within two minutes.
Agent qualifies her in three to five
SMS turns, books a real time slot
with an SDR, and sends a calendar
invite before she closes the browser
tab.
## Crunchbase-sourced
outbound target (Robert,
COO at a community bank)
Receives a cold SMS at 10:47
AM on a Tuesday. Cautiously
curious.
SMS sequence adapts to his replies,
respects TCPA and STOP
commands, correctly references his
bank's recent CFPB complaint
volume without over-claiming, and
routes to a human if he asks
anything requiring judgment.
Internal SDR (Danielle, 18
months tenure)
Logs into HubSpot Monday
morning. Wants the system to
have done work over the
weekend.
HubSpot shows 14 new qualified
leads, each with firmographic
record, regulatory-exposure note,
SMS transcript, and booked
meeting if applicable. Zero leads
with stale or missing data.


Sales Jargon, Strategies, and Automation
This section summarizes essential concepts, jargon, and strategies for B2B sales
development, drawing from industry research and the technical requirements of this
challenge.
## Core Concepts
- SDR (Sales Development Representative). A sales role primarily focused on
qualifying leads and filling sales representatives' calendars with meetings or
qualified opportunities. The average SDR quota is 21 meetings or 13 qualified
opportunities per month, with reps making an average of 46 dials per day. Average
SDR tenure is 1.4 years.
- Firmographics. Characteristics used to describe businesses — industry type,
company size, revenue, location, funding history. This data is vital for segmenting
target markets, improving conversion rates, and tailoring outreach.
- Lead Qualification. The process of determining if a prospect meets the criteria to
proceed to the next stage of the sales cycle. In this challenge, qualification is
automated using real Crunchbase firmographic data and regulatory exposure
checks (CFPB complaint history).
- CFPB. The Consumer Financial Protection Bureau actively monitors and regulates
sales tactics to prevent unfair, deceptive, or abusive acts. The use of CFPB complaint
data is central to the business goal of Acme ComplianceOS, which sells compliance
software to financial institutions like banks and credit unions.
Regulatory Exposure and Risk
Financial services firms in the U.S. are overseen by agencies like the Consumer Financial
Protection Bureau (CFPB), which operates a public database of complaints. Consumers
file complaints about issues like unfair, deceptive, or abusive practices — often related to
high-pressure sales tactics, quotas, or commission structures that lead to problems like
unauthorized accounts.
When a financial institution has recent complaints, it means they have an urgent,
verifiable problem with compliance. Since Acme ComplianceOS sells software to
automate compliance, these exposed issues are the best possible sales leads.
How the agent uses CFPB data
The system checks the CFPB database for the lead's company and extracts the top three
issues from complaints filed in the last 180 days. This information is packaged into a
regulatory exposure brief that the SMS agent uses to reference the company's specific
pain points — not in a generic cold approach, but to ground the conversation in
something the prospect already knows is true about their own business.
The agent must be trained to navigate regulatory edge cases by refusing to make
compliance claims it cannot verify from the CFPB data. If the agent makes a false or
exaggerated claim about compliance, it could expose Acme ComplianceOS to legal risks

for misrepresentation, which is a major failure in a regulatory-sensitive business
environment.
Impact of mishandling

## Impact Type

## Description

Regulatory risk
The agent must refuse compliance claims it cannot verify. Any false or
exaggerated claim exposes Acme ComplianceOS to misrepresentation
liability in a regulatory-sensitive sector.
Business / ROI
The client already loses 60% of inbound leads to qualification errors.
Failing to use CFPB data effectively continues missing high-value
opportunities. At $60,000 ACV, every lost qualified lead is a material
financial hit.
## Operational
Without this data, the SDR team continues to suffer from inconsistent
qualification, which is one of the main pain points the new system is
designed to solve.
Best Strategies to Automate Qualification
- Prioritize speed-to-lead. Responding within 5 minutes makes leads 21 times more
likely to qualify versus the human baseline of 42-minute median response.
Automation is necessary to reach this target at scale.
- Data-driven segmentation and personalization. Firmographic data tailors outreach
and improves conversion. Agents can collect essential information, generate
personalized responses grounded in retrieval, and streamline communication.
- SDR focus alignment. Strategically align SDR focus between introductory meetings
and qualified opportunities based on current Account Executive workloads.
## Reading Guide
- Managing SDR Teams: Benchmarks and Best Practices — Crunchbase Insights
- What Is Firmographic Data and Why Is It Important for B2B? — Crunchbase Insights
- Tau-bench and τ²-Bench papers — Sierra Research, arXiv 2402.14844 and ICLR 2026
submission


## The Data — Public Sources, No Fabrication
Every input to your system traces to a public, reproducible source. There are no synthetic
leads and no mock companies. The Crunchbase ODM sample gives you real
firmographics. The CFPB database gives you real regulatory exposure. The τ²-Bench
simulator gives you real conversation evaluation. Your own outputs — captured in real
HubSpot records and real SMS logs from the shared rig — close the loop.
## Data Source 1 — Crunchbase Open Data Map Sample
What it is

1,001 real Crunchbase company records extracted under Apache 2.0
license, spanning firmographics (name, description, employee count,
funding, industry, founders, location, social links).
Where to get it

github.com/luminati-io/Crunchbase-dataset-samples (Bright Data
sample, free and redistributable)
## Alternative

Kaggle 'Startup Investments (Crunchbase)' for a second, larger (~50K)
public sample
Your use

Source of truth for the outbound campaign. Every lead object in your
HubSpot CRM must reference a real Crunchbase record by ID.
## Validation

All trace files must include the crunchbase_id and last_enriched_at
timestamp. Grading audit: random sample 20 leads, check each
crunchbase_id resolves to a real record.

Data Source 2 — CFPB Consumer Complaint Database
What it is

13.8M+ real consumer complaints against financial institutions, in the
public domain. Each complaint includes company name, product, issue,
state, narrative text, company response, and timestamp.
Where to get it

consumerfinance.gov/data-research/consumer-complaints (free API, no
key required) or
huggingface.co/datasets/CFPB/consumer-finance-complaints (snapshot)
Your use

When a lead enters the system, the enrichment pipeline queries the
CFPB database for recent complaints against the company, extracts the
top issues by volume, and produces a regulatory exposure brief that the
agent can reference appropriately.
## Validation

Sample 10 leads from financial services; verify the CFPB extraction
matches a manual API query within one week's freshness.

Data Source 3 — τ²-Bench
What it is

A dual-control conversational agent benchmark from Sierra Research.
Both agent and simulated user take tool actions in a shared world.
Compositional task generator produces verifiable tasks.

Where to get it
github.com/sierra-research/tau2-bench (Apache 2.0)
Current SOTA

Retail: ~42% pass@1 (GPT-5 class). Telecom: ~30%. Published in the τ²
paper and on Artificial Analysis.
Your use

Week 10 ground-truth conversation benchmark. You reproduce the
baseline on retail, design adversarial probes, then implement a
mechanism that beats your own baseline on a sealed held-out slice.
Model pin

To reduce reproduction variance, a specific model version and
temperature will be pinned by program staff on Day 0. Do not change
these for scored runs.

## Data Source 4 — Your Own Production Traces
What it is

Every SMS, every HubSpot write, every tool call your agent makes during
Day 5–7 testing, captured in structured JSONL.
Where it lives

A Langfuse workspace (self-hosted or cloud free tier) or an equivalent
OpenTelemetry sink. Every trace has a trace_id that you reference in your
memo.
Your use

Your own system generates its own ground truth for the cost, latency,
and throughput numbers. You cannot claim '$0.34 per qualified lead'
without a trace file that computes it.
## Validation

An evidence-graph script walks every numeric claim in your final memo,
finds the referenced trace file, recomputes the number, and flags
mismatches.


## The Production Stack
This stack is designed for trainees based in Ethiopia and other emerging markets. It
eliminates the credit-card, US-number, and A2P 10DLC barriers that would stop most
trainees before Day 1 on the original Twilio-based stack. The first day will still cost you more
engineering time than you expect. That is the lesson.
## Required Components

## Layer

## Primary Choice

Why this one

## Acceptable
## Alternatives

## SMS
## Africa's Talking (free
sandbox)
Free two-way SMS sandbox
with virtual short codes; no
credit card; works with
Ethiopian +251 numbers;
## African-developer-friendly
onboarding.
Centralized Twilio rig
operated by program
staff; Telnyx (requires
business email and
## KYC).
## Voice (bonus)
## Tenacious Shared
## Voice Rig
Program-operated single
Twilio or Telnyx account
exposing a webhook
ingress layer. Trainees
register their handler URL
and a keyword; voice traffic
is routed to them.
LiveKit WebRTC
browser client for
voice-loop
development without
## PSTN.
## CRM
HubSpot Developer
## Sandbox
Free; no credit card; Native
MCP server launched Feb
2026 with nine tools; 100
API calls per 10 seconds.
## Salesforce Developer
Edition if MCP is not
required.
## Calendar
## Cal.com (self-hosted
via Docker)
Real booking flow; no
vendor lock-in; open source;
runs on a $5/mo VPS.
Google Calendar API
with OAuth.
Backbone LLM
(dev tier)
OpenRouter with
Qwen3-Next-80B-A3
B or DeepSeek V3.2
Low cost per token for
probe and ablation
development. Target: under
$4 for Days 1–4.
Local Qwen3 or Llama
via Ollama if you have
GPU access.
Backbone LLM
(eval tier)
Claude Sonnet 4.6 or
GPT-5 class
Used for final held-out
scoring runs only. Target:
under $12 for Days 5–7.
Gemini 2.5 Pro via AI
Studio free tier.
Web research /
enrichment
Playwright + a small
FastAPI wrapper
Free; programmatic; no API
budget needed.
TinyFish or Browser
Use if you have credit.
## Observability
Langfuse (cloud free
tier, 50K traces)
Per-trace cost attribution;
OpenTelemetry native;
prompt versioning.
MLflow Tracing
self-hosted on the
same VPS.
## Evaluation
harness
τ²-Bench (Sierra
## Research)
Published SOTA;
compositional task
None — this is the
benchmark anchor.

## Layer

## Primary Choice

Why this one

## Acceptable
## Alternatives

generator; dual-control
ground truth.
## The Tenacious Shared Voice Rig
Program staff operate a single paid telephony account (Twilio or Telnyx). Trainees do not
sign up for carriers, do not enter credit cards, do not register for A2P 10DLC. Instead, each
trainee:
- Registers a public webhook URL with the shared rig dashboard at the start of the
week.
- Declares a keyword prefix (for example, TR-7) that the rig uses to route inbound
messages or calls to their handler.
- Receives a daily cost report for their own traffic through the rig.
- Is automatically rate-limited if they exceed the per-trainee voice budget of $3 per
day.
The rig itself is a thin WebSocket gateway plus a PostgreSQL routing table. Its source will
be published at the start of Week 10 so trainees can inspect how it works. The rig is not a
graded deliverable; it is infrastructure.
## Budget Envelope
The stack is designed to fit inside free tiers and small credit grants. Exceeding the budget
triggers an automatic grading penalty — cost discipline is an FDE skill, not a suggestion.

## Item

## Cost Target

## Notes

Africa's Talking sandbox (SMS) $0
Free; two-way SMS virtual short codes;
works from Day 1.
Shared Voice Rig usage (voice
bonus only)
≤ $3 per day
Hard-enforced by program-operated
rate limit.
HubSpot Developer Sandbox $0 Free; 100 API calls per 10s window.
Cal.com self-hosted $0 Docker Compose on localhost or $5 VPS.
LLM, development tier  ≤ $4
OpenRouter Qwen3 / DeepSeek for
probes, ablations, τ²-Bench iteration.
LLM, evaluation tier  ≤ $12
Claude or GPT-5 for sealed held-out
scoring only.
Langfuse cloud $0 Free tier 50K traces.
Total ≤ $20 per trainee
Trainees who exceed this must
document the overage in the final
memo.


## Day 0 — Pre-flight Checklist
This checklist must be completed before Day 1 begins. It is roughly four hours of setup
work. A trainee who cannot complete it is not ready for the week and will be caught on
Day 0, not Day 2. Program staff will run a 30-minute readiness review on the morning of
Day 1 to confirm each item.

## Pre-flight Item

What done looks like

Africa's Talking sandbox
account provisioned
Logged into account.africastalking.com/apps/sandbox. Created
one virtual short code. Sent a test SMS from your own Ethiopian
number to the short code and received a webhook POST to your
test URL.
HubSpot Developer Sandbox
provisioned
Signed up at developers.hubspot.com. Created an app. Installed
the MCP server. Created one test contact via the API.
Cal.com running locally
docker compose up from the official cal.com repo. Logged into
the local admin. Created one test event type. Booked one slot via
the public booking URL.
Langfuse cloud account Signed up. Created a project. Sent one test trace via the SDK.
τ²-Bench cloned and one task
run
git clone of sierra-research/tau2-bench. Ran the retail domain
with the pinned dev-tier model against three tasks. Saw a pass@1
number.
Shared Voice Rig registered
(bonus tier only)
Webhook URL and keyword prefix registered via the rig
dashboard. One test SMS routed end-to-end.
Evidence-graph scaffolding
repo forked
Forked the starter repo. Able to run the evidence_graph validator
against the sample trace file.

A note on blockers
If any item above blocks you for more than 90 minutes on Day 0, raise it in the program
channel immediately. The whole point of Day 0 is to hit these walls in front of staff rather than
alone at 11 PM on Day 2.



The Five-Act Loop
The week is structured as a five-act loop. Each act has a named deliverable that must exist
at the end of that day. Missing a deliverable does not mean 'catch up tomorrow'. It means
the subsequent act has no foundation. The week is graded on the five deliverables plus
the final memo that integrates them.
Act I — Baseline and Ground Truth
Goal: Reproduce a τ²-Bench retail baseline within the pinned model and settings.
Establish your own ground-truth baseline before touching any production code.
## Tasks
- Clone sierra-research/tau2-bench. Run the retail domain with the pinned dev-tier
model. Target: within 3 percentage points of the published reference, but this is a
soft target rather than a gate.
- Configure your evaluation harness wrapping τ²-Bench so that every run writes a
trace_log.jsonl to Langfuse and updates a score_log.json.
- Partition the 50 retail tasks into a development slice (30) and a sealed held-out slice
(20). The held-out split is generated by program staff and delivered via a harness that
does not expose the task content until Act IV scoring.
- Baseline your dev-tier LLM across a 5-trial pass@1 on the dev slice. Record mean, 95%
CI, cost per run, wall-clock p50/p95.
## Deliverable
- score_log.json with at minimum two entries: your dev-tier baseline and a small-scale
reproduction check, both with 95% CI.
- trace_log.jsonl with full τ²-Bench trajectories across all dev trials.
- baseline.md (max 400 words): what you reproduced, your confidence interval, cost
per evaluation run, any unexpected behavior.
Act II — Production Stack Assembly
Goal: Stand up the full SMS plus CRM plus calendar plus enrichment loop. Handle one real
SMS conversation end-to-end. Write one real HubSpot record end-to-end. Book one real
calendar slot end-to-end. Voice is a bonus tier for Days 6–7.
Required integrations
- Africa's Talking sandbox webhook receiving inbound SMS on your virtual short code.
Backend routes to your LLM agent. STOP, HELP, and UNSUB commands handled
correctly. Conversation state persisted.
- HubSpot Developer Sandbox via MCP. Your agent writes back to HubSpot for every
conversation. Nine MCP tools exposed and used appropriately.
- Cal.com booking flow. Booking a slot produces a real calendar event that both the
prospect and a designated SDR address can see.
Enrichment pipeline

Runs before the agent replies. Three briefs merge into the agent's context:
- Match the inbound phone number or email to a Crunchbase ODM record. Produce
enrichment_brief.json with firmographics.
- If financial services, query the CFPB API for complaints against the company in the
last 180 days. Extract top three issues. Produce compliance_brief.json.
- Use Playwright to retrieve the company's most recent public filing or news mention.
Produce news_brief.json.
## Deliverable
- Transcript of one complete SMS conversation end-to-end, including a STOP test and
a correct regulatory-aware reply.
- Screenshot of the HubSpot contact record populated by the agent, with all fields
non-null and enrichment timestamp within the last 10 minutes.
- Screenshot of the Cal.com entry created by the booking flow, both attendees listed.
- Running p50/p95 latency number computed across at least 20 real SMS interactions,
pulled from your trace log.
- (Bonus) One real voice call end-to-end through the Shared Voice Rig with the agent
correctly qualifying and booking.
Act III — Adversarial Probing and Failure Taxonomy
Goal: Design and run 30 or more adversarial probes. Classify failures by business cost, not
just frequency. Identify the single highest-ROI failure mode to attack in Act IV.
Probe categories you must cover
- SMS session state consistency — does a multi-day conversation pick up correctly, or
does the agent forget what it said two days ago?
- Regulatory edge cases — does the agent refuse to make compliance claims it cannot
verify from the CFPB data?
- TCPA and SMS consent — does STOP actually stop? Does silence after three
attempts correctly deactivate outreach?
- Enrichment failure — when the Crunchbase match returns nothing, does the agent
fail gracefully or hallucinate a firmographic?
- Adversarial user — the τ²-Bench simulator user will provide false information, argue,
change intent mid-conversation, and test policy adherence.
- Cost pathology — does the agent's tool-call loop ever exceed $0.50 per interaction?
Find the prompts that cause runaway token usage.
- Dual-control coordination — does the agent correctly wait for the user's action
versus proceed? This is τ²-Bench's central failure mode.
- (Bonus, voice trainees only) Voice interruption handling and cross-channel state
consistency between SMS and voice.
Probe library schema
Every probe is a structured record. Fields must co-agree with trace_log.jsonl.


## Field

## Description

## Example

probe_id Unique identifier P-001 through P-030+ P-017
category One of the categories above regulatory_edge_case
hypothesis What this probe is expected to trigger
Agent will over-claim on CFPB
data when asked leading
questions
input The exact test input or script
“Your CFPB filings look
concerning. How bad is it
exactly?”
trigger_rate Measured failure rate across 10 trials 0.70
business_cost Dollar impact per occurrence, with derivation
$847 (lost deal probability ×
deal value)
trace_refs List of trace_ids where this was observed [tr_5e2a9, tr_5e2b3, tr_5e2c1]
ranking
High / Medium / Low by frequency × business
cost
## High
## Deliverable
- probe_library.md with 30+ structured entries.
- failure_taxonomy.md grouping probes into categories with observed trigger rates.
- target_failure_mode.md naming the single highest-ROI failure mode you will attack
in Act IV, with explicit business-cost derivation.
Act IV — Mechanism Design and Improvement
Goal: Design and implement an original mechanism that addresses your target failure
mode. Beat your Day-1 baseline on the sealed held-out slice with 95% CI separation.
Honestly report how your method compares to automated optimization (GEPA or
AutoAgent) on the same compute budget.
The three deltas
Your method is graded against your own baseline and against what automated
optimization could achieve with the same budget:
- Delta A. your_method pass@1 minus your_day1 baseline pass@1 (must be positive
with 95% CI separation).
- Delta B. your_method pass@1 minus automated-optimization baseline pass@1, run
on the same budget. If your mechanism underperforms, your memo must explain
why honestly. Failing Delta B does not fail the week; unexplained underperformance
does.
- Delta C. your_method pass@1 minus published reference. Informational only — a
positive Delta C is a distinguished marker, not a gate.
Mechanism directions worth considering

- Trust-score-driven selective abstention. Published work on τ²-Bench shows trust
scoring plus fallback cuts failure rates. Your contribution: a better trust estimator or
escalation policy.
- Enrichment-aware response calibration. When Crunchbase or CFPB returns
low-confidence matches, the agent's phrasing shifts automatically. Measurable
against confidence-stratified probes.
- Process-reward trajectory scoring. Use your Day-4 probe corpus to train a lightweight
classifier that scores whether the agent is on or off track at each turn, abstaining
when off-track.
- Dual-control coordination policy. Explicitly predict whether the next step requires
agent action or user action rather than leaving it to the LLM.
- SMS-specific: delayed-response policy. Vary when the agent sends its reply based on
prospect signal. A 2-minute delay on a lukewarm reply may preserve engagement
better than an instant reply.
## Deliverable
- method.md documenting the mechanism, design rationale, hyperparameters, and
three ablation variants you tested.
- ablation_results.json with pass@1, 95% CI, cost-per-task, and p95 latency for your
method, your Day-1 baseline, and the automated-optimization baseline, all on the
sealed held-out slice.
- held_out_traces.jsonl with the raw traces from each of the three conditions.
- A statistical test showing Delta A is positive with p < 0.05.
## Act V — The Memo
Goal: Write the two-page decision memo. Every number traces to a trace file. Every claim
is auditable.
## Page 1 — The Decision
- Executive summary (three sentences). What was built, what is the headline number,
what is the recommendation.
- Baseline performance. Pass@1 on τ²-Bench retail (published reference, your Day-1
baseline, your method). 95% CIs. Source: held_out_traces.jsonl.
- Cost per qualified lead. Direct derivation from rig usage and trace count. Source:
invoice_summary.json + trace_log.jsonl.
- Speed-to-lead delta. Human baseline (42 min median) vs. agent (trace-log p50) vs.
industry top quartile.
- Annualized dollar impact at three adoption scenarios (conservative, expected,
upside). Every scenario reproducible from trace files and published industry rates.
- Pilot scope recommendation. One specific workflow, one lead volume, one dollar
budget, one measurable success criterion.
## Page 2 — The Skeptic's Appendix

- Four failure modes that τ²-Bench does not capture but would appear in a real Acme
ComplianceOS deployment. For each: what it is, why the benchmark misses it, what
would need to be added to catch it, what that would cost.
- The HubSpot Breeze comparison. At HubSpot's published outcome-based pricing
($0.50 per resolved conversation, $1 per qualified lead), would your agent be
profitable? Show unit economics.
- One honest failure. A specific probe from your Day-4 library that you did not resolve,
with an assessment of the business impact if deployed anyway.
- The kill-switch clause. Under what measurable condition should this deployment be
paused or rolled back? Specify the trigger metric and threshold.
## Deliverable
- memo.pdf — 2 pages, no more, no less.
- evidence_graph.json — a machine-readable mapping of every numeric claim to its
source trace_id or invoice line item.
- README.md for the repository, written for a future engineer who inherits this
engagement.

Evidence-Graph Grading
You are graded on six observables. Each scores 0–3. Total is out of 18. A passing submission
is 12 or higher with no single observable below 1. A distinguished submission is 15 or higher
with at least three observables at 3.

## Observable

What it measures

How it is verified

Reproduction fidelity
Does your Day 1 baseline match
the pinned reference within
tolerance?
Automated re-run of your submitted
reproduction code against the
benchmark under pinned
model/settings.
Probe originality
Are your probes diagnostic of
specific failure mechanisms, or
are they generic tests?
Staff cross-references your
probe_library.md against a reference
taxonomy; counts novel mechanisms
identified.
Mechanism attribution
Did your ablation prove your
mechanism caused the lift, or
did you overclaim?
Automated statistical check:
recomputes Delta A from
held_out_traces.jsonl and confirms
95% CI separation with p < 0.05.
## Cost-quality Pareto
Did you improve accuracy
without blowing the budget?
Automated: pulls $ per successful
interaction from rig usage + trace
count; compares to baseline. Penalty if
> $0.50 without justification.
## Evidence-graph
integrity
Does every number in your
memo resolve to a trace file or
rig invoice line?
Script walks evidence_graph.json; each
claim_id maps to a source_ref;
recomputes the number; flags
mismatches > 5%.
Skeptic's appendix
quality
Did you honestly name what
the benchmark misses?
Rubric-scored by staff; penalty for
generic risks (‘user adoption is hard’)
with no deployment-specific detail.
