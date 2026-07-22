---
name: brutal-observe
description: Extract evidence-backed candidate Dot Specs from existing code without canonizing implementation accidents. Use when adopting a legacy or code-owned module into the observed or guarded stages, reconciling behavior across code, tests, schemas, docs, and runtime evidence, or preparing a guarded-contract migration for Brutal planning.
---

# Brutal Observe

Transfer behavioral knowledge out of an existing implementation while keeping
code authoritative until selected behavior is explicitly approved and guarded.

## Required Context

1. Read `../brutal-shared/dot-spec-contract.md` and validate the repository's
   `dot_spec` configuration.
2. Read applicable repository rules, ADRs, public interfaces, schemas, tests,
   migrations, operational docs, and available runtime evidence.
3. Read `../brutal-grill/SKILL.md` and `../brutal-wayfinder/SKILL.md`.
4. Require one explicit module boundary. Use wayfinding when evidence gathering,
   access, or contradiction resolution will span multiple sessions.

## Hard Rules

- Treat active code as authority for a `code-owned` module. Observation is not
  an authority transfer.
- Label every candidate statement `observed`, `asserted`, `inferred`, or
  `unknown`; cite its evidence.
- Do not convert missing evidence, inconsistent behavior, or implementation
  accidents into declared requirements.
- Preserve conflicts and unknowns as planning blockers. Never resolve product,
  security, compatibility, or data decisions by majority evidence.
- Do not edit an active canonical spec or promote maturity during observation.

## Observe The Module

1. Inventory public seams, callers, inputs, outputs, state transitions, external
   effects, failure modes, compatibility surfaces, and operational constraints.
2. Gather evidence independently from code, tests, schemas, documentation,
   telemetry or recorded observations, and foreign contracts. Record source,
   snapshot, confidence, and contradictions.
3. Draft candidate requirements with stable proposed ids, concrete scenarios,
   invariants, authority concerns, and the highest public verification seams.
4. Separate four result sets:
   - consistent behavior supported by multiple surfaces
   - behavior supported only by implementation
   - direct contradictions
   - unknown or unobservable intent
5. Add characterization checks for important observed behavior when the user
   authorizes implementation work. A characterization check records behavior;
   it does not declare that behavior desirable.

## Resolve And Guard

Use `brutal-grill` to decide which candidate behaviors are intended, which are
compatibility obligations, which must change, and who owns each authority
concern. Produce an approved semantic change through `brutal-plan`; do not
activate it directly.

The implementation ticket that promotes `observed -> guarded` must land
together:

- selected canonical requirements and provenance
- independent contract or characterization verification
- resolved contradictions and explicitly retained unknowns outside the active
  normative spec
- generated trace evidence
- the guarded maturity update

Merge is the authority-transfer event. Until merge, code remains authoritative.

## Return The Observation Brief

Report the module boundary and snapshot, evidence inventory, candidate
requirements, conflicts, unknowns, characterization gaps, proposed authority
map, and exact decisions required for guarded adoption. Link evidence rather
than copying large artifacts. Mark the brief decision-ready only when every
consequential contradiction is either resolved or an explicit planning blocker.
