---
name: brutal-pr-fix-loop
description: Run a bounded provider-neutral pull-request review and finding-fix loop for up to three passes. Use when the user wants the existing safety-capped Brutal PR cleanup behavior.
---

# Brutal PR Fix Loop

Run the bounded review/fix orchestration without replacing source-skill rules.

## Source Skills

Before starting, read:

- ../brutal-pr-review/SKILL.md
- ../brutal-pr-finding-fixer/SKILL.md

Follow each source skill for its local operation and use this skill only for
ordering and pass accounting.

## Defaults

- Run at most three review/fix passes.
- Use all-findings mode for CRITICAL, MAJOR, MINOR, and NIT.
- Preserve all integration, dirty-worktree, stale-head, fork, verification,
  push, and tooling guards.

## Workflow

1. Resolve the open pull request and integrations through brutal-pr-review.
2. Run an all-findings review and record its review id, head, and validated
   finding count.
3. If the count is zero, stop clean.
4. Run brutal-pr-finding-fixer continuously in all-severity mode.
5. Stop when the fixer made no code-changing commit, no generated occurrence was
   actionable, a hard guard blocked, or pass three completed.
6. If fixes were pushed and fewer than three passes ran, refresh the head and
   repeat.

## Final Response

Report integrations, pull request, final head, stop reason, passes, findings
created/fixed/skipped/blocked by severity, comment actions, commits, checks, and
remaining generated occurrences.

