---
name: brutal-dot-pr-review
description: Review an open pull request against its approved Dot Spec semantic delta while preserving the unchanged Brutal PR Review provider and snapshot workflow. Use for opted-in modules or Dot Spec worker review phases.
---

# Brutal Dot PR Review

Wrap `$brutal-pr-review` with independent semantic verification.

## Preflight

1. Read `../brutal-shared/dot-spec-contract.md` and `../brutal-pr-review/SKILL.md`.
2. Resolve the exact open pull request as the base skill requires.
3. Require the approved change, base SHA, base-spec digests, delta digest, and ticket operations.
4. Stop if the base/head snapshot or approval identity is stale.

## Run The Base Review

Apply `$brutal-pr-review` unchanged for context isolation, reviewer perspectives, finding validation, provider-native posting, and convergence modes.

Add one independent semantic pass that:

- normalizes the base and head spec graphs
- compares the actual semantic diff with approved operations
- verifies authority, provenance, maturity, imports, guards, and activation
- checks independent evidence against the complete base/head snapshot
- classifies drift separately from ordinary implementation defects

Recompute all digests; never trust worker-supplied trace or evidence. Post through the base skill's existing finding and snapshot-safety rules.

## Return

Return the base review result plus semantic parity, evidence status, and any unapproved-contract findings.
