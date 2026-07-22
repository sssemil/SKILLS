---
name: brutal-dot-tickets
description: Decompose an approved Dot Spec semantic delta into cohesive implementation tickets while preserving the unchanged Brutal Tickets workflow. Use after brutal-dot-spec and before Dot Spec plan publication.
---

# Brutal Dot Tickets

Wrap `$brutal-tickets` with exact semantic-operation ownership.

## Preflight

1. Read `../brutal-shared/dot-spec-contract.md` and `../brutal-tickets/SKILL.md`.
2. Require an approved normalized delta whose base and spec digests still validate.
3. Stop if any operation lacks a stable identity or activation boundary.

## Run The Base Skill

Apply `$brutal-tickets` unchanged to choose the fewest cohesive, independently useful scopes and genuine blockers.

Add these fields to each affected ticket:

- change id, delta digest, base SHA, and applicable base-spec digests
- exact non-overlapping requirement operations and module changes
- public seams and traced acceptance criteria
- the single pull request that activates each owned operation
- exact independent verification and evidence requirements

Do not activate a partial cross-ticket requirement before its final blocker. The complete graph must own every approved operation exactly once.

Map every approved logical scope key to exactly one approved ticket scope. After publication, bind provider ticket and pull-request refs outside the normalized semantic delta; do not rewrite the approved keys or digest.

Use the base skill's approval gate and return the approved graph without publishing it.
