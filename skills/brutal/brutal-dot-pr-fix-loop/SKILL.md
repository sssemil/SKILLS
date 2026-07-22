---
name: brutal-dot-pr-fix-loop
description: Run the bounded three-pass review and fix loop for an opted-in Dot Spec pull request while containing every change to its approved semantic delta. Use instead of brutal-pr-fix-loop for Dot Spec work.
---

# Brutal Dot PR Fix Loop

Wrap `$brutal-pr-fix-loop` with Dot Spec review and fix boundaries.

## Preflight

1. Read `../brutal-shared/dot-spec-contract.md` and `../brutal-pr-fix-loop/SKILL.md`.
2. Read `../brutal-dot-pr-review/SKILL.md` and `../brutal-dot-pr-finding-fixer/SKILL.md`.
3. Require one open pull request, approved delta, base SHA, applicable base-spec digests, and exact base/head snapshot.
4. Recompute all identities. Stop before provider writes when any identity is missing, stale, or ambiguous.

## Run The Base Loop

Apply `$brutal-pr-fix-loop` unchanged for its three-pass cap, all-findings mode, pass accounting, provider safety, and stop reasons, with two substitutions:

- every review pass uses `$brutal-dot-pr-review`
- every fix pass uses `$brutal-dot-pr-finding-fixer`

Keep the same approved delta and base identity across all passes. Refresh the head after fixes, recompute the actual semantic diff, and stop `blocked` if it leaves the approved operations. A required semantic change returns to `$brutal-dot-plan`; it never expands the loop.

## Return

Return the base loop report plus change id, approved and actual delta digests, semantic-parity status, evidence status, and any operation returned to planning.
