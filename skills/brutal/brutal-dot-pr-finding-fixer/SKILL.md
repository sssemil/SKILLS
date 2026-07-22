---
name: brutal-dot-pr-finding-fixer
description: Fix generated pull-request findings inside an approved Dot Spec delta while preserving the unchanged Brutal PR Finding Fixer queue and provider workflow. Use for findings on opted-in modules or Dot Spec worker fix phases.
---

# Brutal Dot PR Finding Fixer

Wrap `$brutal-pr-finding-fixer` with semantic-delta containment.

## Preflight

1. Read `../brutal-shared/dot-spec-contract.md` and `../brutal-pr-finding-fixer/SKILL.md`.
2. Resolve the exact generated finding occurrence and approved task operations.
3. Validate the current base/head and approved delta before editing.
4. Stop if the finding requires an unapproved contract, authority, compatibility, activation, or evidence change.

## Run The Base Fixer

Apply `$brutal-pr-finding-fixer` unchanged for queue scans, focused edits, verification, commits, pushes, comments, and dispositions.

After every code-changing fix, recompute the actual semantic diff. Continue only when it equals the approved operations. Strengthening internal tests is allowed only when it does not narrow public behavior beyond the contract.

Return semantic changes to `$brutal-dot-plan` for reapproval instead of expanding fixer scope.

## Return

Return the base fixer report plus actual delta digest, semantic-parity status, evidence status, and any operation returned to planning.
