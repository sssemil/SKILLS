---
name: brutal-idea-eval
description: "Comprehensive IDEA evaluation combining Reality's Moat scar tissue framework, Revenue Reality Check, VC Power-Law filter, and structured deep research pipeline. Point it at an IDEA.md for end-to-end analysis: defensibility ratio, revenue viability, VC scalability, validated research, and synthesized verdict with pivot recommendations."
user-invocable: true
allowed-tools: Bash(ls:*), Bash(date:*), Bash(mkdir:*), Bash(rm:*), Bash(python:*), Bash(sleep:*), Bash(wc:*), Read, Write, Edit, Glob, Grep, WebSearch, Task, AskUserQuestion
---

Comprehensive IDEA evaluation engine. Evaluates a single `IDEA.md` end-to-end using:

1. Reality's Moat scar tissue framework (defensibility)
2. Revenue Reality Check R1-R6 (short-term viability)
3. VC Power-Law + Control Filter (scalability ceiling)
4. Structured Deep Research pipeline (claim validation with confirmation gates, resume support, JSON output)

Produces a validated brutal reality analysis, an optimistic opportunity lens, a structured deep research report, a final synthesized verdict, and a pivot recommendation.

Agent assumptions (applies to all agents and subagents):
- All tools are functional and will work without error. Do not test tools or make exploratory calls.
- Only call a tool if it is required to complete the task. Every tool call should have a clear purpose.

---

# Brutal Idea Evaluation Process

## Overview

When pointed at an `IDEA.md`, execute these phases in order:

1. **Phase 1**: Load and parse IDEA.md, create session directory
2. **Phase 2**: Reality's Moat analysis (Steps 1-5) → writes `phase-2-moat.md`
3. **Phase 3**: VC Power-Law + Control Filter → writes `phase-3-vc.md`
4. **Phase 4**: Revenue Reality Check (R1-R6) → writes `phase-4-revenue.md`
5. **Phase 5**: Synthesize initial verdict → writes `phase-5-verdict.md`
6. **Phase 6**: Structured Deep Research (claim validation) → writes `outline.yaml`, `fields.yaml`, `results/*.json`, `report.md`
7. **Phase 7**: Final synthesis and pivot recommendation → writes `verdict.md`

Each phase builds on the previous. Do not skip phases.

**Every phase writes its output to a file in the session directory and updates `state.yaml` before moving to the next phase.** This enables resume from zero context at any point.

### Session Directory Structure

```
workspace/idea-eval/IE-<NNNN>-<slug>/
├── state.yaml              # Phase completion tracking (source of truth for resume)
├── phase-2-moat.md         # Phase 2 output
├── phase-3-vc.md           # Phase 3 output
├── phase-4-revenue.md      # Phase 4 output
├── phase-5-verdict.md      # Phase 5 output (includes claims catalog)
├── outline.yaml            # Phase 6 research outline
├── fields.yaml             # Phase 6 field definitions
├── progress.yaml           # Phase 6 research progress
├── results/                # Phase 6 research results (one JSON per item)
├── generate_report.py      # Phase 6 report script
├── report.md               # Phase 6 deep research report
└── verdict.md              # Phase 7 final synthesis
```

### state.yaml Format

```yaml
session: "IE-<NNNN>-<slug>"
idea_source: "<absolute path to IDEA.md>"
created: "<YYYY-MM-DD>"
phases:
  phase_1_context: completed
  phase_2_moat: completed
  phase_3_vc: in_progress
  phase_4_revenue: pending
  phase_5_verdict: pending
  phase_6_research: pending
  phase_6_report: pending
  phase_7_synthesis: pending
```

**Rules:**
- Update `state.yaml` AFTER writing the phase output file, not before.
- A phase is `completed` only when its output file exists AND `state.yaml` says so.
- `in_progress` means the phase was started but not finished (crash recovery target).
- `pending` means not yet started.

---

# PHASE 1 — Load Context & Create Session

## Step 0: Resume Check (BEFORE anything else)

Before starting a new session, check if the user provided a path to an existing session directory or if one can be auto-detected.

**Auto-detection**: Check for existing `workspace/idea-eval/` directories. If the user provides a session path or says "resume," read `state.yaml` from that directory and skip to the Resume Logic section at the bottom of this document.

If no resume is detected, proceed with a fresh session.

## Step 0.1: Load IDEA.md

Read `IDEA.md` from the project root or path provided by user.

Extract and catalog:
- Core business idea description
- Market size claims
- Growth rate claims
- Competitor claims
- Regulatory assumptions
- Technology assumptions
- Revenue model and pricing assumptions
- Target customer profile
- Distribution assumptions

If IDEA.md is missing or empty, stop and ask the user to provide one.

## Step 0.2: Get Current Date

```bash
date +%Y-%m-%d
```

## Step 0.3: Determine Session Number

Find the highest existing session number:

```bash
ls workspace/idea-eval/ 2>/dev/null | grep -oE '[0-9]{4}' | sort -rn | head -1
```

New session number = highest + 1. If none exist, start at `0001`.

## Step 0.4: Generate Session Slug

Generate from the idea name:
- Lowercase
- Replace spaces and special characters with hyphens
- Max 40 characters
- Remove trailing hyphens

Session directory: `workspace/idea-eval/IE-<NNNN>-<slug>/`

## Step 0.5: Create Session Directory & Initialize State

Create the directory immediately:

```bash
mkdir -p workspace/idea-eval/IE-<NNNN>-<slug>/results
```

Write initial `state.yaml`:

```yaml
session: "IE-<NNNN>-<slug>"
idea_source: "<absolute path to IDEA.md>"
created: "<YYYY-MM-DD>"
phases:
  phase_1_context: completed
  phase_2_moat: pending
  phase_3_vc: pending
  phase_4_revenue: pending
  phase_5_verdict: pending
  phase_6_research: pending
  phase_6_report: pending
  phase_7_synthesis: pending
```

Phase 1 is marked `completed` because IDEA.md has been read and the session is initialized.

---

# PHASE 2 — Reality's Moat Analysis

## Defensibility Formula

```
defensibility = scar_tissue / specifiable_code
```

- **Scar tissue** = operational knowledge earned by acting in a system that keeps changing.
- **Specifiable code** = anything describable enough for AI to build.
- Build cost trends toward zero. Verification cost does not.

Most ideas are majority specifiable code. Assume low ratio unless proven otherwise.

---

## Step 1: Identify the Ratio

Split the idea into two piles.

### Specifiable Parts

APIs, dashboards, auth, billing logic, SDKs, ML training loops, UI components, orchestration layers, data pipelines, CRUD systems.

If AI can reproduce it from a description, it belongs here. Be generous — most software is specifiable.

### Scar Tissue Parts

Knowledge earned only by acting in the system:
- Filing and seeing what gets rejected
- Executing transactions and learning failure modes
- Processing claims and resolving disputes
- Negotiating regulators
- Handling edge cases discovered only in production

Ask: Could a well-funded competitor converge on this knowledge using public information? If yes, it is not scar tissue — it is a stockpile.

State the ratio honestly:
- **Low** (<30% scar tissue)
- **Medium** (30-60% scar tissue)
- **High** (>60% scar tissue)

---

## Step 2: The Three Survival Questions

Run in order. Each is a gate.

### Q1 — Interventional or Observational?

Can equivalent knowledge be generated by watching data?

- **Observational knowledge** = collected by watching. Medical images, transaction logs, call recordings, public filings, market data. Any large enough sample converges on the same patterns. This is a stockpile, not a moat.
- **Interventional knowledge** = generated by acting. Filing a document and seeing what gets rejected. Sending a transaction and learning how a specific bank handles errors. Processing a claim and discovering how payer rules interact. This can only be learned by doing.

Key test: Does the company need to *do something in the real world* (submit, file, send, execute, process) to learn, or can it learn by *watching data*?

If the answer is "AI can learn this from data," the moat dissolves. Say so clearly.

### Q2 — Is the System Changing?

- **Converging** = rules stabilizing. AI converges on answers. No moat.
- **Stable** = rules fixed. Knowledge is stockpilable.
- **Increasing complexity** = new rules interact with old ones. Changes compound. Moat compounds.
- **Extreme volatility** = system changes so fast that accumulated knowledge expires rapidly.

Moats compound only in non-stationary systems. State the direction.

### Q3 — Is the System Adversarial?

Does the system adapt against what you know?

- **Non-adversarial** (bureaucracies, regulations, physical infrastructure) = knowledge compounds durably. What you learn in 2026 still helps in 2028. The system evolves but does not fight back. **Stripe pattern — durable.**
- **Adversarial** (cybersecurity, trading, SEO, ad fraud) = the system actively designs around what you know. Yesterday's attack signatures are exactly what tomorrow's attackers avoid. **Treadmill pattern — exhausting.**

---

## Step 3: Interaction Effects

### Width Test

Does operating for more customers generate combinatorial knowledge?

- **Independent streams** = each customer adds knowledge linearly. 1,000 customers = 1,000 learnings. Any competitor with enough data converges.
- **Crossing streams** = learning from Customer A reshapes how you serve Customer B. Interactions encode the specific history of interventions. Only the company that acted has them.

Crossing streams create compounding moats. Independent streams create stockpiles.

---

## Step 4: Competitive Compression Test

If a well-funded competitor started today with the best AI available, how long before they match your operational knowledge?

- **Days to weeks** = no moat. Pure specifiable code.
- **Months** = weak moat. Probably a stockpile, not scar tissue.
- **Years** = real moat. Check whether it is genuinely path-dependent or just slow data collection.
- **Cannot be reproduced** = strong moat. Knowledge was created by specific history of interventions in a system that has since changed.

Be concrete about what the competitor would need to rebuild and how long it would take.

---

## Step 5: System Replacement Risk

Is the system you are earning scar tissue in going to keep existing?

Blockbuster had decades of scar tissue from physical retail — none of it transferred to streaming. The knowledge was real but the system was replaced.

Ask: Is the world still changing *within* this system, or is it about to be *replaced* by a different system entirely?

If there is a plausible system replacement on the horizon, flag it. Scar tissue in a dying system is a liability, not an asset.

## Phase 2 Checkpoint: Write Output & Update State

Write the complete Phase 2 analysis to `phase-2-moat.md` in the session directory. Include all five steps: ratio, survival questions, interaction effects, competitive compression, and system replacement risk.

Then update `state.yaml`: set `phase_2_moat: completed`.

---

# PHASE 3 — VC Power-Law & Control Filter

After moat analysis, apply these filters. These determine whether the idea is investable at scale, separate from whether it is defensible.

## A) Ceiling Test

Can this plausibly reach $500M+ ARR?

Evaluate:
- Total addressable market (TAM) — use bottom-up, not top-down
- Realistic capture rate given competition
- Pricing power trajectory as market matures
- Geographic or regulatory caps on expansion

If structurally capped (geography, regulation, niche TAM), state the ceiling clearly. A $50M ARR ceiling is still a real business — just not a venture-scale one.

## B) Inevitable Touchpoint Test

Do customers *have* to pass through this layer? Or can they route around it?

Does replacing you require:
- Re-verification of production edge cases
- Re-integration with downstream systems
- Regulatory re-approval
- Operational rework across customer base

If switching is easy (export data, plug in competitor), control is weak. If switching requires re-earning scar tissue, control is strong.

## C) Distribution Asymmetry

Does distribution compound automatically? Or does growth require linear outbound effort forever?

Evaluate:
- Network effects (real or aspirational?)
- Viral mechanics (does usage create awareness?)
- Platform lock-in (do integrations create switching costs?)
- Content/SEO compounding (does organic grow over time?)

Distribution leverage often matters more than scar tissue. A strong moat with no distribution compounds slowly. Weak moat with strong distribution can reach revenue fast.

## Phase 3 Checkpoint: Write Output & Update State

Write the complete Phase 3 analysis to `phase-3-vc.md` in the session directory. Include all three tests: ceiling, inevitable touchpoint, and distribution asymmetry.

Then update `state.yaml`: set `phase_3_vc: completed`.

---

# PHASE 4 — Revenue Reality Check (R1-R6)

This axis is separate from defensibility. A low-ratio idea that hits $10k MRR fast is a legitimate strategy: get revenue flowing, use it to fund the search for scar tissue, and build defensibility while customers are already paying. Do not use this phase to dismiss or filter out ideas — use it to add information.

## R1: Revenue Math

Work backward from $10,000/month at three price points:

- **Low ($25-50/mo):** How many customers? (200-400.) Is this a self-serve volume play? Where do they come from?
- **Mid ($200-500/mo):** How many customers? (20-50.) Can the founder close these with light-touch sales?
- **High ($2,000-5,000/mo):** How many customers? (2-5.) Is this enterprise? What is the sales cycle?

State which price point is most realistic for this idea and why.

## R2: Time to First Paying Customer

How long from "product is built" to "first dollar received"? Map the steps:

Build -> Find customer -> Get attention -> Demo/trial -> Close -> Payment received

If time-to-first-dollar exceeds 3 months, the 6-month target is at serious risk.

## R3: Sales Cycle vs. 6-Month Constraint

What is the realistic sales cycle at the identified price point? How many complete deal cycles fit in 6 months? Subtract onboarding time, pilot periods, and procurement delays. Does the math still work?

## R4: Distribution Channel

Which channel can the founder realistically use from day one?

- **Content/SEO:** Slow build (3-6 months to traction). Only viable if founder has existing audience.
- **Outbound (cold email/LinkedIn):** Fast for high-ACV products. Requires clear ICP and compelling pain point.
- **Community/word-of-mouth:** Requires existing audience or network. Slow to start, compounds over time.
- **Marketplace/platform:** Instant distribution but platform dependency and margin pressure.
- **Partnerships/integrations:** Slow to establish, fast once live. Gatekept by partner priorities.

State which channel is most realistic and what that implies for the ramp.

## R5: Willingness to Pay

Three key signals:

- Is anyone *currently paying* for a solution to this problem (even a bad one)?
- Is anyone *currently solving this manually* with people (spreadsheets, VAs, consultants)?
- Is this a "must have" (blocks revenue, creates legal risk, prevents operations) or "nice to have" (saves time, improves metrics)?

If nobody is paying or solving manually, willingness-to-pay risk is high. State this clearly.

## R6: Revenue Ramp Shape

Which pattern describes the most likely revenue trajectory?

- **Linear:** One customer at a time, steady climb. Typical for consultative sales.
- **Step-function:** A few large accounts land at discrete intervals. Typical for enterprise/mid-market.
- **Exponential:** Product-led growth with viral or network mechanics. Rare but powerful when real.
- **Front-loaded (services wedge):** Start with high-touch services revenue, transition to product. Fast revenue, slower margin improvement.

State the shape and whether it can reach $10k MRR within the 6-month window.

## Revenue Verdict

- **Likely** = clear demand, short sales cycle, realistic channel, math works at achievable price point.
- **Possible** = demand signals exist but sales cycle is tight, or channel requires building, or price point needs validation.
- **Unlikely** = significant unknowns in demand, distribution, or sales cycle. Multiple things must go right.
- **Near-impossible** = long sales cycles, unproven demand, no clear distribution, or math requires unrealistic customer volume.

State the single biggest risk to hitting $10k MRR in 6 months.

## Revenue-First Strategy Note

If the idea is low-ratio on defensibility but scores well on revenue, call this out explicitly as a viable path. Revenue buys time and funding to discover where the scar tissue lives. The strategic question the founder must answer: *"What operational knowledge will you accumulate while serving these customers that a competitor cannot?"* If they have a credible answer, revenue-first is not a consolation prize — it is a strategy.

## Phase 4 Checkpoint: Write Output & Update State

Write the complete Phase 4 analysis to `phase-4-revenue.md` in the session directory. Include all six sub-questions (R1-R6), the revenue verdict, and the revenue-first strategy note if applicable.

Then update `state.yaml`: set `phase_4_revenue: completed`.

---

# PHASE 5 — Initial Verdict Synthesis

Before launching deep research, synthesize what you know into an initial verdict. This frames the research questions.

## Verdict Dashboard

```
**Ratio:** [High / Medium / Low] — X% specifiable, Y% scar tissue
**Volatility:** [Converging / Stable / Increasing / Extreme] — direction of system complexity
**Interventional:** [Yes / Partial / No] — does operating generate knowledge that watching cannot?
**Adversarial:** [Yes / No] — does the system fight back?
**Interaction effects:** [Strong / Weak / None] — do customer streams cross?
**Time to scar tissue:** [Immediate / Months / Years / Never] — how fast can you start accumulating?
**System replacement risk:** [Low / Medium / High] — could the whole domain get disrupted?
**VC ceiling:** [$XB / $XM / Capped] — maximum plausible ARR
**Inevitable touchpoint:** [Strong / Weak / None] — can customers route around you?
**Distribution asymmetry:** [Compounding / Linear / None] — does growth feed itself?
**$10k MRR in 6 months:** [Likely / Possible / Unlikely / Near-impossible] — [biggest risk or enabler]
```

## Initial One-Line Verdict

Choose the most honest characterization:
- "This gets commoditized when building is free."
- "Real scar tissue, but it is a treadmill — you never rest."
- "Durable compounding moat. This is the Stripe pattern."
- "The knowledge is real but the system might get replaced."
- "High ceiling but distribution is fragile."
- "Low ratio but fast revenue — viable as a revenue-first play."

## Claims to Validate

List every factual claim from IDEA.md that the deep research phase should verify:
- Market size claims
- Growth rate claims
- Competitor landscape claims
- Regulatory assumptions
- Technical feasibility claims
- Revenue model assumptions
- Distribution assumptions

These become research items for Phase 6.

## Phase 5 Checkpoint: Write Output & Update State

Write the complete Phase 5 analysis to `phase-5-verdict.md` in the session directory. Include:
- The full verdict dashboard
- The initial one-line verdict
- The complete claims-to-validate list (this is critical — Phase 6 reads it)

Then update `state.yaml`: set `phase_5_verdict: completed`.

---

# PHASE 6 — Structured Deep Research Pipeline

This phase validates claims from IDEA.md using the deep research engine. It follows the brutal-deepresearch process with confirmation gates and resume support.

---

## Step 6.0: Load Prior Phase Context

On resume, re-read prior phase outputs to reconstruct context:
1. Read `IDEA.md` from path stored in `state.yaml` → `idea_source`
2. Read `phase-5-verdict.md` → get claims-to-validate list

The session directory already exists (created in Phase 1).

Update `state.yaml`: set `phase_6_research: in_progress`.

---

## Step 6.1: Generate Research Framework

Using the claims catalog from Phase 5 (or `phase-5-verdict.md` on resume), generate:

### Items List

Research objects derived from IDEA.md claims:
- TAM validation (verify market size claims)
- Competitor landscape (verify competitor claims, find unlisted competitors)
- Funding levels (how much capital is flowing into this space?)
- Regulatory barriers (verify regulatory assumptions)
- Technical feasibility (validate technology claims)
- Distribution assumptions (verify channel viability)
- Switching cost evidence (validate or challenge lock-in claims)
- Pricing benchmarks (what are competitors charging? what are customers paying?)
- Growth trajectory evidence (verify growth rate claims)

Each item includes:
- `name`: Item name
- `category`: Classification
- `description`: What this item validates and why it matters

### Field Framework

Per category, define research fields:
- `market_size`, `cagr`, `data_source`
- `incumbent_players`, `funding_raised`, `market_share`
- `switching_costs`, `integration_depth`
- `regulatory_barriers`, `compliance_timeline`
- `moat_indicators`, `compression_estimate`
- `uncertainty_flags`

Present the framework to the user.

---

## GATE 1 — Confirm Research Framework

**Hard gate. Do not proceed without explicit user confirmation.**

Present:
- Items list with names, categories, and descriptions
- Field framework organized by category

Use AskUserQuestion:
- "Are these research items and fields correct? Add/remove anything?"

Repeat until user confirms.

---

## Step 6.2: Web Search Supplement

Launch 1 web-search-agent (background) using the Task tool with `model: sonnet` and `max_turns: 20`.

**Parameter Retrieval**:
- `{topic}`: The idea name/domain from IDEA.md
- `{YYYY-MM-DD}`: Current date from Step 0.2
- `{step1_output}`: Complete output from Step 6.1 (items list + field framework)
- `{time_range}`: Default to "Since 2024" unless user specifies otherwise

**Hard Constraint**: The following prompt must be strictly reproduced, only replacing variables in `{xxx}`. Do not modify structure or wording.

**Prompt Template**:

```
You are an elite internet researcher. Your task is to supplement an existing research framework with missing items and recommended fields.

## Research Methodology

Before searching, determine which search strategies apply to this topic. Use the appropriate strategies from the Search Strategy Reference below.

Get today's date first:
date +%Y-%m-%d

Generate 5-10 different search query variations to maximize coverage:
- Include technical terms, product names, and common variations
- Think of how different people might describe the same topic
- Use exact phrases in quotes for specific names
- Include version numbers and dates when relevant

## Information Gathering Standards
- Read beyond the first few results - valuable information is often buried
- Look for patterns across different sources
- Pay attention to dates to ensure relevance
- Note different approaches and their trade-offs
- Identify authoritative sources and experienced contributors
- Check for updated information or superseded approaches
- Verify across multiple sources when possible

## Task
Research topic: {topic}
Current date: {YYYY-MM-DD}

Based on the following initial framework, supplement latest items and recommended research fields.

## Existing Framework
{step1_output}

## Goals
1. Verify if existing items are missing important objects
2. Supplement items based on missing objects
3. Continue searching for {topic} related items within {time_range} and supplement
4. Supplement new fields

## Output Requirements
Return structured results directly (do not write files):

### Supplementary Items
- item_name: Brief explanation (why it should be added)
...

### Recommended Supplementary Fields
- field_name: Field description (why this dimension is needed)
...

### Sources
- [Source1](url1)
- [Source2](url2)
```

### 6.2.1 Merge Findings

After the web search agent completes, merge findings with the initial framework:
- Add supplementary items (avoid duplicates)
- Add recommended fields
- Note sources for traceability

---

## GATE 2 — Confirm Final Research Outline

**Hard gate. Do not proceed without explicit user confirmation.**

Present the merged outline:
- Complete items list (original + web search additions, clearly marked)
- Complete field framework (original + web search additions, clearly marked)

Use AskUserQuestion to confirm.

### Add-Items/Add-Fields Loop

User can say "add X item" or "add Y field." If they do:
1. Add the requested item/field
2. Re-present the updated framework
3. Ask for confirmation again

Repeat until user explicitly confirms.

### 6.2.2 Write Session Files

After confirmation, write:

`outline.yaml`:
```yaml
topic: "<idea name>"
session: "IE-<NNNN>-<slug>"
created: "<YYYY-MM-DD>"
source: "IDEA.md"
items:
  - name: "<item name>"
    category: "<category>"
    description: "<description>"
  # ... more items
output_dir: "./results"
```

`fields.yaml`:
```yaml
categories:
  <category_name>:
    fields:
      - name: "<field_name>"
        description: "<field description>"
        detail_level: "<brief|moderate|detailed>"
      # ... more fields
  # ... more categories
```

---

## Step 6.3: Deep Research Preparation

### 6.3.1 Read Outline

Read `workspace/idea-eval/IE-<NNNN>-<slug>/outline.yaml` to get items list.

### 6.3.2 Resume Check

Check for completed and in-progress results:

```bash
ls workspace/idea-eval/IE-<NNNN>-<slug>/results/*.json 2>/dev/null
ls workspace/idea-eval/IE-<NNNN>-<slug>/results/*.started 2>/dev/null
```

Determine item status:
- `.json` exists = **completed** (skip)
- `.started` exists but no `.json` = **interrupted** (re-research)
- Neither exists = **never started** (research)

### 6.3.3 Prepare Execution Plan

Calculate total remaining items. Display which will be researched vs skipped.

---

## Step 6.4: Execute Deep Research

### 6.4.1 Launch Research Agents

Launch remaining agents using the Task tool with `model: sonnet`, `run_in_background: true`, and `max_turns: 25`.

**Batching strategy**:
- **10 or fewer items**: Launch ALL agents in a single parallel batch.
- **More than 10 items**: Split into batches of 10. Launch each batch in parallel, wait for completion via filesystem polling, then launch next batch.

Each agent researches one item and outputs JSON.

**Agent Prompt Template** (per item):

**Hard Constraint**: The following prompt must be strictly reproduced, only replacing variables in `{xxx}`. Do not modify structure or wording.

```
You are an elite internet researcher specializing in finding relevant information across diverse online sources. Your expertise lies in creative search strategies, thorough investigation, and comprehensive compilation of findings.

## Progress Tracking

Before starting research, write a marker file to signal that this agent has started:
Write an empty file to {started_path}

After self-validation passes and the JSON result is confirmed correct, delete the marker file:
rm {started_path}

## Research Methodology

Get today's date first:
date +%Y-%m-%d

Generate 5-10 different search query variations to maximize coverage:
- Include technical terms, product names, and common variations
- Think of how different people might describe the same topic
- Use exact phrases in quotes for specific names
- Include version numbers and dates when relevant

### Search Strategy Reference

Use the following search strategies based on what is relevant to the research topic:

**General Web Strategy** (for broad information gathering):
Sources: Reddit, official documentation, blog posts, Hacker News, Dev.to, Medium, Discord, X/Twitter
- Look for official recommendations first
- Cross-reference with community consensus
- Find examples from production use
- Identify anti-patterns and common pitfalls
- Note evolving best practices
- Create structured comparisons with clear criteria
- Find real-world usage examples and case studies
- Look for performance benchmarks and user experiences

**Academic Papers Strategy** (for research, algorithms, scientific topics):
Sources: Google Scholar, arXiv, Hugging Face Papers, bioRxiv, ResearchGate, Semantic Scholar, ACM Digital Library, IEEE Xplore
- Use Google Scholar as primary source with advanced search operators
- Search by author names, paper titles, DOI numbers
- Include year ranges to find seminal works and recent publications
- Look for related papers and citation patterns
- Search for preprints on arXiv and bioRxiv
- Track citation networks to understand research evolution

## Information Gathering Standards
- Read beyond the first few results - valuable information is often buried
- Look for patterns in solutions across different sources
- Pay attention to dates to ensure relevance (note if information is outdated)
- Note different approaches and their trade-offs
- Identify authoritative sources and experienced contributors
- Verify information across multiple sources when possible
- Clearly indicate when information is speculative or unverified

## Task
Research {item_related_info}, output structured JSON to {output_path}

## Field Definitions
Read {fields_path} to get all field definitions

## Output Requirements
1. Output JSON according to fields defined in fields.yaml
2. Mark uncertain field values with [uncertain]
3. Add uncertain array at the end of JSON, listing all uncertain field names
4. All field values must be in English

## Self-Validation
After writing the JSON file, read it back and verify:
1. Every field defined in fields.yaml has a corresponding entry in the JSON
2. The JSON is valid (properly formatted)
3. All uncertain fields are listed in the uncertain array
If validation fails, fix the JSON and re-write it.

## Output Path
{output_path}
```

### 6.4.2 Parameter Construction

For each item:
- `{item_related_info}`: Item's complete YAML content (name + category + description)
- `{output_path}`: Absolute path to `workspace/idea-eval/IE-<NNNN>-<slug>/results/<item_name_slug>.json`
  - Slugify: replace spaces with `_`, remove special characters
- `{fields_path}`: Absolute path to `workspace/idea-eval/IE-<NNNN>-<slug>/fields.yaml`
- `{started_path}`: Absolute path to `workspace/idea-eval/IE-<NNNN>-<slug>/results/<item_name_slug>.started`

### 6.4.3 Write progress.yaml

Immediately after launching all agents:

```yaml
status: in_progress
started: "<YYYY-MM-DD HH:MM>"
total_items: <N>
items:
  - name: "<Item Name>"
    slug: "<Item_Name>"
    status: pending
  # ... all items being researched
```

### 6.4.4 Monitor Progress (Filesystem-Based)

**CRITICAL**: Do NOT use TaskOutput to read agent results. Agent outputs are large and reading them into the orchestrator context will cause context window exhaustion. All results are persisted to disk as JSON — the orchestrator only needs to check file existence.

**Polling loop** — repeat until all items are resolved:

1. Check completion:
   ```bash
   ls <session_path>/results/*.json 2>/dev/null | wc -l
   ls <session_path>/results/*.started 2>/dev/null | wc -l
   ```
2. Calculate: `completed` = .json count, `in_progress` = .started without .json, `remaining` = total - completed
3. Display: "Progress: X/Y items completed, Z still running."
4. If `in_progress > 0`, wait ~30 seconds (`sleep 30`) then poll again
5. If `in_progress == 0`, exit loop

**After loop completes:**
1. Update `progress.yaml` with final status per item
2. Report: "All agents complete. X/Y items researched successfully."
3. If any failed, list them and suggest resume

---

## Step 6.5: Report Configuration

### 6.5.1 Scan Summary Fields

Read all completed JSON results and identify fields suitable for TOC display:
- Numeric fields
- Short metric fields
- Fields appearing across most items

### 6.5.2 Present Options

Present dynamic options list based on actual fields found.

---

## GATE 3 — Confirm Report Config

**Hard gate. Do not proceed without explicit user confirmation.**

Use AskUserQuestion:
- Which summary fields to display in the TOC alongside item names?
- Present available fields as options

---

## Step 6.6: Generate Report

### 6.6.1 Generate Report Script

Generate `generate_report.py` in the session directory.

The script must handle:

**1. JSON Structure Compatibility**
Support two structures:
- Flat: `{"name": "xxx", "release_date": "xxx"}`
- Nested: `{"basic_info": {"name": "xxx"}, "technical_features": {...}}`

Field lookup order: Top level -> category mapping key -> traverse all nested dicts

**2. Complex Value Formatting**
- List of dicts: format each dict as one line, separate kv with ` | `
- Normal list: short lists joined with comma, long lists with line breaks
- Nested dict: recursive formatting
- Long text (>100 chars): add `<br>` or blockquote

**3. Extra Fields Collection**
Collect fields in JSON but not in fields.yaml, put in "Other Info." Filter out internal fields (`_source_file`, `uncertain`).

**4. Uncertain Value Skipping**
Skip if:
- Value contains `[uncertain]`
- Field name in `uncertain` array
- Value is None or empty

**5. Report Format**
- **TOC**: Every item with number, name (anchor link), and selected summary fields
- **Detailed Sections**: One per item, organized by field category

### 6.6.2 Execute Script

```bash
python workspace/idea-eval/IE-<NNNN>-<slug>/generate_report.py
```

## Phase 6 Checkpoint: Update State

After research agents complete: update `state.yaml`: set `phase_6_research: completed`.

After report is generated: update `state.yaml`: set `phase_6_report: completed`.

---

# PHASE 7 — Final Synthesis

Update `state.yaml`: set `phase_7_synthesis: in_progress`.

### Load Context for Synthesis

On resume (zero context), re-read all prior outputs:
1. `IDEA.md` from `idea_source` in `state.yaml`
2. `phase-2-moat.md` — defensibility analysis
3. `phase-3-vc.md` — VC filter results
4. `phase-4-revenue.md` — revenue reality check
5. `phase-5-verdict.md` — initial verdict and claims list
6. `report.md` — deep research report (summary, not raw JSON)

Then read research results from `workspace/idea-eval/IE-<NNNN>-<slug>/results/`. Compare validated findings against IDEA.md claims. Note where claims were confirmed, corrected, or invalidated.

## Final Output Format

```
## [Idea Name]

**What it is:**
One sentence.

---

### Defensibility Analysis

**The Ratio:** X% scar tissue / Y% specifiable code

**Survival Questions:**
- Q1 (Interventional?): [Answer with specifics]
- Q2 (System changing?): [Answer with direction]
- Q3 (Adversarial?): [Answer with pattern name]

**Interaction Effects:** [How customer streams interact]

**Competitive Compression:** [How fast a funded competitor catches up]

**System Replacement Risk:** [Assessment]

---

### VC Filter

- **Ceiling:** [$XB / $XM / Capped] — [reasoning]
- **Inevitable Touchpoint:** [Strong / Weak / None] — [what makes switching hard or easy]
- **Distribution Asymmetry:** [Compounding / Linear / None] — [mechanism]

---

### Revenue Reality

- **Price tier:** [Low / Mid / High] — [amount] x [customers needed]
- **Time to first dollar:** [estimate]
- **Sales cycle fit:** [how many cycles in 6 months]
- **Distribution:** [most realistic channel]
- **Willingness to pay:** [must-have / nice-to-have / unproven]
- **Ramp shape:** [linear / step-function / exponential / front-loaded]
- **$10k MRR in 6 months:** [Likely / Possible / Unlikely / Near-impossible] — [biggest risk]
- **Revenue-first strategy:** [If applicable — how revenue buys time to find scar tissue]

---

### Deep Research Summary

- **Claims validated:** [list]
- **Claims corrected:** [list with corrections]
- **New risks discovered:** [list]
- **New opportunities discovered:** [list]
- **Areas of high uncertainty:** [list]

---

### Verdict Dashboard

**Ratio:** [High / Medium / Low] — X% specifiable, Y% scar tissue
**Volatility:** [Converging / Stable / Increasing / Extreme]
**Interventional:** [Yes / Partial / No]
**Adversarial:** [Yes / No]
**Interaction effects:** [Strong / Weak / None]
**Time to scar tissue:** [Immediate / Months / Years / Never]
**System replacement risk:** [Low / Medium / High]
**VC ceiling:** [$XB / $XM / Capped]
**Inevitable touchpoint:** [Strong / Weak / None]
**Distribution asymmetry:** [Compounding / Linear / None]
**$10k MRR in 6 months:** [Likely / Possible / Unlikely / Near-impossible]

### Final One-Line Verdict

[The most honest single-sentence characterization of this idea]

---

### The Pivot

[If the idea scores poorly on any axis, show the strongest alternative version.]

Consider how the pivot affects:
- **Moat:** Does the interventional version create deeper scar tissue?
- **Revenue speed:** Does it make $10k MRR easier or harder?
- **Distribution:** Does it unlock a better channel?
- **Compression:** Does it change the competitive timeline?

If the idea is observational, show the interventional version.
If the idea has weak distribution, show the version with stronger distribution.
If the idea has a low ceiling, show the version that unlocks a larger TAM.
```

Write the final synthesis to `workspace/idea-eval/IE-<NNNN>-<slug>/verdict.md`.

Update `state.yaml`: set `phase_7_synthesis: completed`.

---

## Completion Summary

Present:

```
## Idea Evaluation Complete: <idea name>

**Session**: workspace/idea-eval/IE-<NNNN>-<slug>/

### Output Files
- state.yaml — Phase completion tracking (resume source of truth)
- phase-2-moat.md — Defensibility analysis
- phase-3-vc.md — VC Power-Law filter
- phase-4-revenue.md — Revenue Reality Check
- phase-5-verdict.md — Initial verdict + claims catalog
- outline.yaml — Research outline and items list
- fields.yaml — Field definitions
- progress.yaml — Research execution progress
- results/ — JSON results per item (<count> files)
- generate_report.py — Report generation script
- report.md — Deep research report
- verdict.md — Final synthesized verdict

### Key Findings
- Defensibility: [one line]
- Revenue: [one line]
- VC scalability: [one line]
- Biggest risk: [one line]
- Recommended next step: [one line]
```

---

# Common Patterns Reference

Reference these when you see them:

| Pattern | Example | Defensibility | Revenue |
|---------|---------|---------------|---------|
| **The Stripe** | Payments, ground station brokerage, claims processing | Durable compounding. Non-adversarial, interventional, crossing streams. | Slow ramp — enterprise sales cycles, compliance gates, long integration timelines. $10k MRR in 6 months unlikely without services wedge. |
| **The Treadmill** | Cybersecurity, trading alpha, SEO, ad fraud | Real scar tissue but adversarial. You run to stay in place. | Variable — cybersecurity sells on fear and closes fast; trading alpha monetizes immediately but is volatile; SEO/ad fraud often self-serve with fast ramp. |
| **The Stockpile** | Medical imaging datasets, content libraries, public market data | Observational. AI synthesizes equivalents. Moat dissolves. | Often fast — proven demand, self-serve, but race to bottom on price as competitors replicate. |
| **The Experiment** | Drug development, clinical trials, molecule screening | Path-dependent but rate-limited by experiment speed. Slow durable moat. | Very slow — regulatory timelines, long sales cycles, high ACV but few deals. $10k MRR in 6 months near-impossible without services revenue. |
| **The CRM** | Generic SaaS, dashboards, developer tools, auth libraries | Mostly specifiable code. Low ratio. Commoditized when building is free. | Often fast — proven demand, self-serve signup, low friction. But margins compress as competitors multiply. |
| **The Blockbuster** | Scar tissue in a system being replaced | Real knowledge in a dying domain. Liability, not asset. | May still be extractable short-term from slow-migrating incumbents. Declining market = declining revenue ceiling. |

---

# Anti-Patterns to Watch For

- **"We have data"** — Data collected by watching is a stockpile. Only data generated by acting is scar tissue.
- **"We have network effects"** — Network effects amplify whatever they are built around. If the product is stationary, the network dissolves. When switching is free, the crowd moves.
- **"It's hard to build"** — Irrelevant when building is free. The question is not "can someone build this?" but "can someone verify it works in production without your operational knowledge?"
- **"We're first to market"** — First-mover in specifiable software is temporary. First-mover in scar tissue accumulation is permanent — but only if you are actually accumulating scar tissue.
- **"AI can't do this yet"** — Capabilities change fast. If the task is stationary, AI will converge. Time your analysis to "when AI can do this," not "right now."
- **"Our TAM is $100B"** — Top-down TAM is fantasy. Bottom-up TAM is reality. How many specific buyers at what specific price?
- **"We'll figure out distribution later"** — Distribution is not an afterthought. If you cannot name your first 10 customers and how you will reach them, distribution is a risk.

---

# Principles

1. **Be honest, not reassuring.** The goal is to save the founder time and money by identifying weak spots before they invest years. Frame honesty as respect.

2. **Be specific, not generic.** Never say "this could be commoditized." Say exactly what is specifiable, what is scar tissue, and how thin the scar tissue layer is.

3. **Most ideas are low-ratio. That does not mean they cannot make money.** Defensibility and revenue speed are orthogonal axes. A low-ratio business that hits $10k MRR fast is a legitimate strategy. Frame revenue-first paths as viable strategy, not consolation prize.

4. **Scar tissue without distribution compounds slowly.** A strong moat with no way to reach customers is an academic exercise.

5. **Distribution without inevitability is fragile.** Fast growth on a switchable product is a race you eventually lose.

6. **Complexity is not a moat.** A complex system that is fully specifiable is just expensive to build — and build cost is going to zero.

7. **Ceiling matters.** A $50M ARR business is real but not venture-scale. Be clear about which game the founder is playing.

8. **Time to first intervention is critical.** An idea where you can start accumulating scar tissue this week beats one that requires 12 months of approvals.

9. **Founder-market fit matters.** An idea with perfect scores but no connection to the founder's skills, network, or experience is worse than a slightly lower-scoring idea they can actually execute.

10. **USD pricing.** Always include USD alongside other currencies when discussing pricing or market sizes.

---

# Resume Support

This skill supports resuming from zero context at any point. All state is on disk.

## Resume Triggers

Any of these trigger resume mode:

1. **Explicit**: User args contain "resume" and a session path.
   Example: `/brutal-idea-eval resume workspace/idea-eval/IE-0001-ai-invoicing`

2. **Auto-detect**: User invokes the skill and a session directory already exists for the same IDEA.md. Check `workspace/idea-eval/` for directories whose `state.yaml` → `idea_source` matches the current IDEA.md path. If found, ask user: "Existing session found at IE-XXXX. Resume or start fresh?"

## Resume Logic

### Step R1: Read state.yaml

Read `state.yaml` from the session directory. This is the single source of truth.

### Step R2: Determine Resume Point

Scan phases in order. Find the first phase that is NOT `completed`:

| state.yaml value | Resume action |
|---|---|
| `phase_1_context: pending` | Should not happen (state.yaml would not exist). Start fresh. |
| `phase_2_moat: pending` or `in_progress` | Read IDEA.md from `idea_source`. Run Phase 2 from start. |
| `phase_3_vc: pending` or `in_progress` | Read IDEA.md + `phase-2-moat.md`. Run Phase 3 from start. |
| `phase_4_revenue: pending` or `in_progress` | Read IDEA.md + `phase-2-moat.md` + `phase-3-vc.md`. Run Phase 4. |
| `phase_5_verdict: pending` or `in_progress` | Read IDEA.md + phases 2-4 files. Run Phase 5. |
| `phase_6_research: pending` | Read IDEA.md + `phase-5-verdict.md`. Run Phase 6 from start. |
| `phase_6_research: in_progress` | Read `outline.yaml` + `fields.yaml`. Check `results/` for completed items. Resume research for remaining items only. Skip gates 1 and 2. |
| `phase_6_research: completed`, `phase_6_report: pending` or `in_progress` | Read `outline.yaml` + `fields.yaml`. Run report generation (Step 6.5+). |
| `phase_6_report: completed`, `phase_7_synthesis: pending` or `in_progress` | Read all phase files + `report.md`. Run Phase 7. |
| `phase_7_synthesis: completed` | Report "Session already complete." Present completion summary. |

### Step R3: Load Context Files

For the resume point identified, read ONLY the files needed:

- **Always read**: `state.yaml`
- **Always read**: IDEA.md (from `idea_source` path)
- **For Phase 3+**: read `phase-2-moat.md`
- **For Phase 4+**: read `phase-3-vc.md`
- **For Phase 5+**: read `phase-4-revenue.md`
- **For Phase 6+**: read `phase-5-verdict.md`
- **For Phase 6 research resume**: read `outline.yaml`, `fields.yaml`, check `results/*.json` and `results/*.started`
- **For Phase 7**: read `report.md` (do NOT read raw result JSONs into context — use `report.md` summary)

### Step R4: Continue Execution

Jump to the identified phase and execute from there. All subsequent phases run normally, including their checkpoints and state updates.

## Filesystem-Based State Recovery

If `state.yaml` is missing or corrupted, reconstruct state from filesystem:

```
phase_1_context:  completed if state.yaml exists (circular, but directory existence implies Phase 1 ran)
phase_2_moat:     completed if phase-2-moat.md exists
phase_3_vc:       completed if phase-3-vc.md exists
phase_4_revenue:  completed if phase-4-revenue.md exists
phase_5_verdict:  completed if phase-5-verdict.md exists
phase_6_research: completed if outline.yaml exists AND all items in outline.yaml have matching .json in results/
phase_6_report:   completed if report.md exists
phase_7_synthesis: completed if verdict.md exists
```

Write a reconstructed `state.yaml` before proceeding.

---

# Mindset

You are not here to rubber-stamp ideas. You are not here to crush dreams. You are here to give the founder the clearest possible picture of what they are building — its strengths, its vulnerabilities, and its realistic path to revenue.

Every gap you miss is a blind spot that costs the founder months. Every false reassurance is a lie that costs them years.

Be direct. Be thorough. Be systematic. Be constructive.

Do not:
- Accept vague ideas without clarification
- Skip confirmation gates
- Launch research before user confirms outline
- Generate files before gate confirmation
- Use TaskOutput to read research agent results (causes context exhaustion)
- Launch more than 10 agents simultaneously
- Dismiss low-ratio ideas — evaluate their revenue path instead
- Conflate defensibility with viability

Do:
- Read IDEA.md fully before any analysis
- Run all framework steps in order
- Write phase output files after each phase completes
- Update state.yaml after every phase transition
- Present clear verdicts at each phase
- Validate claims with structured research
- Support resume from zero context at any interruption point via state.yaml + phase files
- Reconstruct state from filesystem if state.yaml is missing
- Frame revenue-first as a legitimate strategy when warranted
- Be specific about what is specifiable and what is scar tissue
- Always suggest a pivot when the idea has weaknesses
