---
name: brutal-inf-fix-loop
description: Review and fix an open pull request without a pass limit until a fresh review has no CRITICAL or MAJOR findings. When material findings exist, drain every severity opportunistically; a final MINOR/NIT-only pass is materially clean and may stop.
---

# Brutal Infinite Fix Loop

Run an uncapped material-correctness loop. “Infinite” removes arbitrary pass and
no-progress caps; it does not require polishing MINOR/NIT findings forever.

## Source Skills

Read `../brutal-pr-review/SKILL.md` and
`../brutal-pr-finding-fixer/SKILL.md` before starting. Follow their safety and
provider rules.

## Convergence Contract

- Review every pass for CRITICAL, MAJOR, MINOR, and NIT findings.
- Continue while the fresh pass contains at least one CRITICAL or MAJOR.
- When material findings exist, publish and drain all four severities from that
  pass. Lower-severity findings are worth fixing while a material cycle is
  already required.
- Stop successfully when a fresh pass has zero CRITICAL and zero MAJOR.
  - No findings at all: `completion_kind: zero_findings`.
  - MINOR/NIT only: `completion_kind: materially_clean`. Put the residuals in
    the review summary and task record; do not create actionable finding
    comments for them.
- Do not impose a pass, elapsed-time, token, cost, commit, or no-progress limit.
- A hard source-skill guard stops `blocked`; user interruption stops `canceled`.

## Managed Tmux Mode

Do not run the whole loop inside one Codex thread. Obey the phase manifest from
the supervisor, validate its digest/artifacts, and perform only that phase:

- `review`: run one fresh material-convergence review and return a checkpoint
  with base/head snapshot, review id, counts by severity, queue counts, and
  residual MINOR/NIT findings.
- `fix`: drain the complete generated queue for that review occurrence, verify,
  push, and return a checkpoint.

The supervisor derives `review -> fix` when CRITICAL+MAJOR is nonzero and
`review -> handoff` otherwise. Never choose or request the next phase yourself.
Return the exact managed result and exit, echoing the v3 context digest when
present. Retained v2 attempts keep their v2 result. Same-thread resume is only
for an interrupted attempt in the same phase.

## Standalone Or Native Mode

1. Reuse validated integrations and the exact open pull request when supplied;
   otherwise resolve them through BRUTAL.md.
2. Run one fresh `brutal-pr-review` material-convergence pass.
3. If CRITICAL+MAJOR is zero, stop with the appropriate completion kind.
4. Drain every generated severity with `brutal-pr-finding-fixer` until no
   unhandled occurrence remains or a hard guard blocks.
5. Re-resolve the pull request and latest head, even if no commit was made, and
   return to step 2.

Progress updates contain only pass, base/head snapshot, severity counts,
fixed/skipped totals, commits, verification status, and blocker state. Redirect
verbose test, diff, and provider output to run-local temporary logs. Report
status and duration; on failure include only the last 200 lines or 16 KiB,
whichever is smaller.

## Final Response

Report integrations, pull request, final base/head snapshot, total passes,
completion kind, counts fixed/skipped by severity, residual MINOR/NIT findings,
commits, verification, and final review id. On a hard stop, include the exact
blocker and remaining generated occurrences; never describe it as clean.
