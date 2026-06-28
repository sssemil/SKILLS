---
name: gh-brutal-pr-fix-loop
description: "Loop gh-brutal-pr-review and gh-brutal-pr-finding-fixer passes until generated PR findings are fixed or a safety stop is reached."
---

# GH Brutal PR Fix Loop

Run a strict review/fix loop for a GitHub PR using the backend context resolved
from `BRUTAL.md`.

## Source Skills

Before starting, read:

- `../gh-brutal-pr-review/SKILL.md`
- `../gh-brutal-pr-finding-fixer/SKILL.md`

If either source skill conflicts with this skill, follow the source skill for
the local operation and use this skill only for loop ordering.

## Defaults

- Run at most 3 review/fix passes.
- Use all-findings mode so concrete line-mappable `CRITICAL`, `MAJOR`, `MINOR`,
  and `NIT` findings may be queued.
- Keep cleanup concrete and behavior-preserving.
- Respect source-skill safety stops for dirty worktrees, stale PR heads,
  fork/external PRs, incomplete thread state, push rejection, backend ambiguity,
  and unavailable required tooling.

## Workflow

1. Resolve the target PR using `gh-brutal-pr-review` rules.
2. Run `gh-brutal-pr-review` in all-findings mode with:
   ```json
   "inline_severities": ["CRITICAL", "MAJOR", "MINOR", "NIT"]
   ```
3. Run `gh-brutal-pr-finding-fixer` in continuous all-severities mode.
4. Stop when no generated inline findings were actionable, the fixer made no
   code-changing commit, a safety guard blocked, or pass 3 completed.
5. If fixes were pushed and the pass count is below 3, repeat review.

## Final Response

Report PR, backend/context ref, final head SHA, stop reason, passes completed,
comments created/patched, findings fixed/skipped/blocked by severity, commit
hashes, verification results, and remaining generated findings if known.
