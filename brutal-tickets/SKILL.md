---
name: brutal-tickets
description: Decompose an approved specification into the smallest useful dependency graph of cohesive, decision-complete implementation scopes. Use when another Brutal planning skill needs executable tasks, or when the user wants an approved plan split into implementation tickets without publishing them yet.
---

# Brutal Tickets

Design implementation work that a fresh agent can complete one ticket at a
time. Require an approved, decision-complete specification before starting.

## Draft Cohesive Scopes

Make one ticket own one coherent outcome. Keep its schema, API, services,
callers, UI, migration, cleanup, and tests together when they must be reasoned
about, landed, or verified together. Ticket count follows the work; it is not a
planning target.

Split a scope only when the parts have different hard blockers, ownership,
rollout boundaries, or independently valuable outcomes. File count, crate or
layer boundaries, implementation phases, parallelism, and context-window size
do not justify a split by themselves.

Treat ordinary implementation order inside one outcome as a checklist, not a
ticket dependency. If neither proposed ticket is useful or complete without the
other, merge them.

Each ticket must:

- deliver a complete observable or verifiable outcome
- depend only on work that genuinely blocks it
- preserve a green integration state when it lands
- give a fresh agent enough decisions and verification to finish or resume it

Use the fewest scopes that satisfy these conditions. Prefer a checklist inside
one ticket over several tickets that only make sense together.

### Wide refactors

Use expand-contract inside one cohesive ticket when one migration owns the
whole change:

1. expand by adding the new form beside the old
2. migrate callers in independently green batches sized by blast radius
3. contract by removing the old form after every migration batch

Create separate expand, migration, or contract tickets only when those phases
must land or roll out independently. Otherwise keep the sequence and its final
verification in the same ticket.

## Define Each Ticket

Use this body contract:

```markdown
## Parent
## Phase And Order
## What To Build
## Acceptance Criteria
## Blocked By
## Implementation Notes
## Verification Commands
```

Describe end-to-end behavior in `What To Build`; keep layer-by-layer detail in
implementation notes. Use stable module and interface names rather than guessed
paths. Make acceptance criteria externally observable and verification commands
exact. Express dependencies as ticket titles until backend identifiers exist.

## Approval Gate

Present a numbered graph in dependency order with one line per ticket: cohesive
scope, delivered outcome, and blockers. Keep complete bodies and the acceptance
coverage trace ready for publication, but show them only when the user asks.
Ask the user to approve the scope boundaries, granularity, blocking edges,
coverage, and any merge or split decisions.

Iterate until approved. The stage completes only when every ticket is
decision-complete, every blocking edge is necessary, and the graph covers every
spec acceptance criterion. Return the approved graph without publishing it.
