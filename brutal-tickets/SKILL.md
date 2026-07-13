---
name: brutal-tickets
description: Decompose an approved specification into a dependency graph of decision-complete tracer-bullet implementation tickets. Use when another Brutal planning skill needs executable tasks, or when the user wants an approved plan split into vertical slices without publishing them yet.
---

# Brutal Tickets

Design implementation work that a fresh agent can complete one ticket at a
time. Require an approved, decision-complete specification before starting.

## Draft Tracer Bullets

Prefer narrow vertical slices that cross every necessary layer and leave an
observable, testable behavior working. Each slice must:

- fit in one fresh context window
- be independently demonstrable or verifiable
- depend only on work that genuinely blocks it
- preserve a green integration state when it lands

Put enabling prefactors first when they make later behavior changes materially
simpler. Do not create horizontal tickets for all schema, all API, all UI, or
all tests.

### Wide refactors

When one mechanical change has a blast radius that prevents vertical slices,
use expand-contract:

1. expand by adding the new form beside the old
2. migrate callers in independently green batches sized by blast radius
3. contract by removing the old form after every migration batch

If migration batches cannot stay green independently, make them share an
integration branch and block a final integrate-and-verify ticket.

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

Present a numbered graph in dependency order, then the complete proposed body of
every ticket. Include a trace showing which tickets cover each specification
acceptance criterion. Ask the user to approve the full ticket contents,
granularity, blocking edges, coverage, and any merge or split decisions.

Iterate until approved. The stage completes only when every ticket is
decision-complete, every blocking edge is necessary, and the graph covers every
spec acceptance criterion. Return the approved graph without publishing it.
