---
name: brutal-dot-inf-fix-loop
description: Review and fix an opted-in Dot Spec pull request without a pass limit until a fresh semantic review has no CRITICAL or MAJOR findings. Use as the Dot Spec-safe replacement for brutal-inf-fix-loop.
---

# Brutal Dot Infinite Fix Loop

Wrap `$brutal-inf-fix-loop` without allowing review or fixes to escape the approved semantic delta.

## Preflight

1. Read `../brutal-shared/dot-spec-contract.md` and `../brutal-inf-fix-loop/SKILL.md`.
2. Read `../brutal-dot-pr-review/SKILL.md` and `../brutal-dot-pr-finding-fixer/SKILL.md`.
3. Require one open pull request, approved delta, base SHA, applicable base-spec digests, and exact base/head snapshot.
4. Recompute all identities. Stop before provider writes when any identity is missing, stale, or ambiguous.

## Run The Base Loop

Apply `$brutal-inf-fix-loop` unchanged for convergence, pass accounting, managed phases, provider safety, and completion kinds, with two substitutions:

- every review pass uses `$brutal-dot-pr-review`
- every fix pass uses `$brutal-dot-pr-finding-fixer`

Keep the same approved delta and base identity across all passes. Refresh the head after fixes, recompute the actual semantic diff, and stop `blocked` if it leaves the approved operations. A required semantic change returns to `$brutal-dot-plan`; it never expands the loop.

## Return

Return the base loop report plus change id, approved and actual delta digests, semantic-parity status, evidence status, and any operation returned to planning.
