---
name: brutal-dot-spec
description: Convert a decision-complete requirements brief into an approved, base-bound Dot Spec semantic delta while preserving the unchanged Brutal Spec workflow. Use after brutal-dot-grill for opted-in modules.
---

# Brutal Dot Spec

Wrap `$brutal-spec` with an immutable semantic-change contract.

## Preflight

1. Read `../brutal-shared/dot-spec-contract.md` and `../brutal-spec/SKILL.md`.
2. Require a decision-complete `$brutal-dot-grill` brief and a valid opted-in module graph.
3. Normalize the active graph and record the repository base SHA and applicable spec digests.
4. Stop on unknown normative behavior, ambiguous authority, or stale evidence.

## Run The Base Skill

Apply `$brutal-spec` unchanged to synthesize and stress-test the behavioral and technical contract.

Then encode its accepted changes as complete requirement-level `add`, `replace`, or `remove` operations. Encode maturity, authority-map, import, and default-seam changes as explicit module changes. Give every operation one stable logical scope key and one stable activation scope key. These keys express ownership before provider tickets or pull requests exist.

Validate and normalize the delta with the configured Dot Spec command. Record its schema version, change id, base identity, approval identity, and digest.

## Approval

Use the base skill's approval gate. Approval freezes the normalized delta; it does not edit the active canonical spec. Any later semantic difference requires reapproval.

Return the approved base specification and the immutable Dot Spec delta without publishing either.
