---
name: brutal-dot-grill
description: Resolve requirements for an opted-in Dot Spec module while preserving the unchanged Brutal Grill workflow. Use when planning a Dot Spec feature, migration, authority transfer, compatibility change, or maturity promotion that still has material decisions.
---

# Brutal Dot Grill

Wrap `$brutal-grill` with Dot Spec evidence and authority constraints.

## Preflight

1. Read `../brutal-shared/dot-spec-contract.md` and `../brutal-grill/SKILL.md`.
2. Resolve `dot_spec` from `BRUTAL.md` without changing the base integration resolver.
3. Validate the configured manifest and identify every affected opted-in module.
4. Stop if configuration is missing, the module is not listed, or validation fails. Never fall back to ordinary Brutal behavior inside this wrapper.

## Run The Base Skill

Apply `$brutal-grill` unchanged for repository investigation, decision rounds, scope, risks, acceptance scenarios, and invariants.

Extend its decision-complete brief with:

- stable requirement ids and affected authority concerns
- provenance and evidence without treating observed behavior as desired behavior
- current maturity and proposed promotion
- compatibility classification and public seams
- base-spec identity, intended semantic operations, and activation boundaries
- independent verification surfaces

Keep `unknown` in investigation artifacts only. Send unresolved evidence to `$brutal-observe` or `$brutal-wayfinder`.

## Return

Return the base requirements brief plus the validated module set and Dot Spec decisions. Do not write an active spec or approve a semantic delta.
