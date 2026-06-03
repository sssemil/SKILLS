---
name: linear-brutal-project-review
description: Systematically reviews a project subsystem-by-subsystem and creates Linear review finding issues for CRITICAL and MAJOR problems.
---

Linear-backed brutal project review. Use this when the user asks for
`$linear-brutal-project-review`, asks to review a project into Linear, or asks
for brutal-project-review behavior without local review-state/task files.

This skill preserves the subsystem-by-subsystem review discipline of
`brutal-project-review`, but Linear is the only persistent review state.

## Hard Rules

- First read the repo's `AGENTS.md`.
- `AGENTS.md` must name the Linear project to use. Accept clear wording such as
  `Linear project: <name>` or "Use the Linear project `<name>`".
- If the Linear project name is missing, stop and ask the user to add or provide
  it. Do not guess.
- Resolve the project through Linear MCP before creating review artifacts.
- If Linear MCP tools are unavailable, stop and report that review findings
  cannot be persisted. Do not fall back to local files.
- Never create new `workspace/review-state`, `workspace/tasks`, or
  `workspace/plans` files.
- Use only these labels: `type:plan`, `type:task`, `type:review-finding`.
- Put severity, subsystem, component, source, confidence, and file references in
  issue bodies/comments, not labels.
- Create Linear issues only for CRITICAL and MAJOR findings by default.

## Step 0: Resolve Project Context

1. Read `AGENTS.md`.
2. Extract and resolve the Linear project name.
3. Read referenced workflow docs if present.
4. Read `TARGET.md` if present.
5. Check git status and note uncommitted changes; do not edit files during the
   review workflow unless the user explicitly changes the request.

## Step 1: Discover Subsystems

Discover subsystems dynamically from source files. Do not hardcode subsystem
names.

Include common source and config files:

- Rust, TypeScript, JavaScript, CSS, JSON, SQL, TOML, Markdown docs that define
  architecture or service behavior

Exclude generated/vendor/build folders:

- `.git`, `target`, `node_modules`, `dist`, `build`, `.next`, `coverage`,
  `vendor`

Derive subsystem paths from package/service boundaries such as:

- `crates/<component>/<crate>/`
- `apps/<name>/`
- `libs/<name>/`
- nearest package root that owns the source files

Present a concise subsystem table and ask the user which to review:

- one subsystem by id/name/path
- `pending`
- `all`
- `restart`
- `cancel`

If a prior Linear review run exists for this project, use it as context, but do
not require it to proceed.

## Step 2: Create Or Update Review Run In Linear

For a fresh review, create a parent Linear issue labeled `type:plan` with title:

```text
Project Review: <repo or project name>
```

Body:

```markdown
Source: linear-brutal-project-review

## Review Scope
<selected subsystem list>

## Status
- Pending: <count>
- In Progress: <count>
- Complete: <count>

## Notes
Review findings are created as child or related issues with label `type:review-finding`.
```

When Linear project documents are available, create a review manifest document
with subsystem status and link it from the parent issue. If documents are not
available, keep review run state in comments on the parent issue.

## Step 3: Gather Subsystem Context

For each selected subsystem:

- list source files
- read relevant files fully enough to review them
- include applicable repo rules from `AGENTS.md`
- include related tests, migrations, APIs, clients, configs, and docs

Use `/tmp/linear-project-review-<subsystem-slug>.md` for ephemeral subagent
context if subagents are used. Do not persist context in the repo.

## Step 4: Run Multi-Perspective Review

Launch parallel review subagents when available. Perspectives:

- Core logic and architecture
- Reliability, tests, and error handling
- Cleanliness, documentation, and repo rules
- Performance and security
- Code reduction and simplicity

Each finding must include:

- severity: CRITICAL, MAJOR, MINOR, or NIT
- confidence 0-100
- file and line reference
- code snippet when useful
- concrete explanation
- actionable fix

Severity definitions:

- `CRITICAL`: must fix before merge; correctness, data loss, security, or
  forbidden production panic/unwrap patterns
- `MAJOR`: should fix; significant design, reliability, performance, or test
  gap
- `MINOR`: worthwhile but not blocking
- `NIT`: optional cleanup

## Step 5: Synthesize And Validate Findings

Before creating Linear issues:

- combine duplicate findings
- filter false positives
- validate file/line references against current code
- downgrade or drop speculative findings
- ensure suggested fixes are concrete

Number findings as:

```text
<subsystem-slug>-001
<subsystem-slug>-002
```

## Step 6: Persist Review Results In Linear

Write a subsystem report as either a Linear document or a parent issue comment:

```markdown
# Review: <Subsystem>

Reviewed: <timestamp>

## Summary
- CRITICAL: <count>
- MAJOR: <count>
- MINOR: <count>
- NIT: <count>

## Findings
...
```

For each CRITICAL or MAJOR finding, create a Linear issue:

- label: `type:review-finding`
- status: `Todo`
- project: resolved Linear project
- parent or related issue: review parent issue when supported

Issue title:

```text
Fix <subsystem>: <brief finding>
```

Issue body:

```markdown
Source: linear-brutal-project-review
Subsystem: <subsystem path/name>
Severity: <CRITICAL|MAJOR>
Finding ID: <subsystem-slug>-001
Confidence: <0-100>
File: `<path>:<line>`

## Issue
<validated explanation>

## Suggested Fix
<specific fix>

## Acceptance Criteria
- [ ] Investigate and confirm the issue
- [ ] Implement the fix
- [ ] Add or update tests if applicable
- [ ] Run repo verification
```

Do not create issues for MINOR/NIT findings unless the user asks.

## Step 7: Final Response

Report:

- subsystem reviewed
- finding counts by severity
- Linear review parent issue/document
- created CRITICAL/MAJOR issue identifiers
- recommended next subsystem or `$linear-task-worker` for fixes

Be direct and findings-first. Avoid praise and vague summaries.
