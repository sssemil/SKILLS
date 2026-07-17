---
name: brutal-inf-fix-loop
description: Review and fix every generated finding on the current feature branch's open pull request until a fresh all-severity review is completely clean. Use when the user wants an uncapped Brutal fix loop with no pass or no-progress limit.
---

# Brutal Infinite Fix Loop

Continue the provider-neutral review/fix cycle until there is nothing left to
complain about.

## Source Skills

Before starting, read:

- ../brutal-pr-review/SKILL.md
- ../brutal-pr-finding-fixer/SKILL.md

Follow each source skill for review and fix operations. Use this skill only for
unbounded ordering and termination.

## Invariants

- Require an open pull request for the current feature branch.
- Review every pass in all-findings mode: CRITICAL, MAJOR, MINOR, and NIT.
- Declare success only after a fresh review returns validated_finding_count: 0.
- Do not impose a pass, elapsed-time, token, cost, commit, or no-progress limit.
- Do not stop because a fixer pass produced no commit, every occurrence was
  skipped, or the same fingerprint recurred.
- Preserve hard source-skill guards. A safety or dependency failure stops
  blocked; user interruption stops canceled.

## Loop

1. Reuse a caller's validated integrations, canonical local work-store root,
   and exact pull request when supplied. Otherwise resolve BRUTAL.md, the code
   host, work store, and current open pull request.
2. Run brutal-pr-review in all-findings mode against a fresh head snapshot.
3. If the review reports zero validated findings, stop successfully.
4. Run brutal-pr-finding-fixer continuously across all severities until the
   current generated queue is drained or a hard guard blocks.
5. Re-resolve the pull request and its latest head even when no code-changing
   commit was made.
6. Return to step 2 without applying any arbitrary limit.

After each pass, give only a concise progress update with pass number, reviewed
head, findings by severity, fixes/skips, commits, and current blocker state.
Do not turn a progress update into a terminal response while the loop remains
eligible to continue.

## Final Response

On a clean review, report integrations, pull request, final head, total passes,
findings fixed/skipped by severity, commits, verification, and the zero-finding
review id. On a hard stop or user interruption, report the same data plus the
exact blocker and remaining generated occurrences; never describe that outcome
as clean.
