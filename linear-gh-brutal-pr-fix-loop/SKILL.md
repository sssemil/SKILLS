---
name: linear-gh-brutal-pr-fix-loop
description: Loop Linear-aware GitHub PR brutal reviews and generated finding fixes. Use when Codex is asked to run repeated linear-gh-brutal-pr-review plus linear-gh-brutal-pr-finding-fixer passes, fix all generated PR findings, rerun review after fixes, polish Rust code idiomatically, trim fluff, reduce needless optionality, or continue until no review findings remain.
---

# Linear GH Brutal PR Fix Loop

Run a strict review/fix loop for a GitHub PR tied to Linear context. This skill
only adds orchestration. Preserve every guardrail, safety check, posting rule,
commit rule, and final-response requirement from the source skills.

## Source Skills

Before starting, read both files in full and keep their instructions active:

- `/home/user/Workspaces/SKILLS/linear-gh-brutal-pr-review/SKILL.md`
- `/home/user/Workspaces/SKILLS/linear-gh-brutal-pr-finding-fixer/SKILL.md`

If either source skill conflicts with this skill, follow the source skill for
the local operation and use this skill only to decide loop ordering.

## Defaults

- Run at most 3 review/fix passes.
- Stop earlier when no actionable generated finding remains.
- Use all-findings mode: generated `CRITICAL`, `MAJOR`, `MINOR`, and `NIT`
  findings may be queued and fixed.
- Keep cleanup concrete and behavior-preserving. Prefer smaller, idiomatic Rust
  and less needless optionality, but do not rewrite code for subjective taste.
- Respect normal source-skill safety stops for dirty worktrees, stale PR heads,
  fork/external PRs, incomplete thread state, push rejection, Linear ambiguity,
  and unavailable required tooling.

## Workflow

### Step 1: Initialize The Loop

Resolve the target PR using `linear-gh-brutal-pr-review` rules. Record:

- PR number, URL, branch, base branch, and head SHA
- Linear issue identifier
- current pass number, starting at 1
- commits pushed and findings handled across all passes

Do not continue if the review skill would stop before reviewing.

### Step 2: Run Review In All-Findings Mode

Run `linear-gh-brutal-pr-review` exactly as specified, with these additions:

- Ask reviewers to produce only concrete, validated findings.
- For Rust changes, emphasize ownership, error handling, async safety,
  allocation, API minimality, idiomatic standard-library use, and removal of
  avoidable fluff.
- When creating the `post_github_review.py` payload, include:

```json
"inline_severities": ["CRITICAL", "MAJOR", "MINOR", "NIT"]
```

Only line-mappable findings become generated inline queue items. Keep unmappable
or cross-file findings in the generated summary.

### Step 3: Drain Generated Findings

Run `linear-gh-brutal-pr-finding-fixer` in continuous all-severities mode.
Process generated inline findings in this order:

1. `CRITICAL`
2. `MAJOR`
3. `MINOR`
4. `NIT`

For each finding, preserve the fixer contract: validate the finding, make the
smallest correct change, run focused verification, create one focused commit,
push normally, and reply with the handled marker. If one code change clearly
handles related fingerprints, reply to each related finding with the same
disposition so it is not selected again.

### Step 4: Decide Whether To Repeat

After the fixer stops, re-fetch the PR state through the source-skill rules.

Stop when any condition is true:

- no generated inline findings were actionable
- the fixer made no code-changing commit in the pass
- a source-skill safety guard blocked
- pass 3 completed

If fixes were pushed and the pass count is below 3, increment the pass number
and return to Step 2. If pass 3 pushed fixes, stop at the cap and report that no
fourth review was run.

## Final Response

Report:

- PR, Linear issue, final head SHA, and stop reason
- passes completed and whether the 3-pass cap was reached
- review summaries posted and inline comments created or patched
- findings fixed, skipped, or blocked by severity
- commit hashes pushed by the loop
- verification commands and results
- remaining generated findings, if known

Keep the response concise, but include blockers and remaining risk plainly.
