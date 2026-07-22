---
name: brutal-plan
description: Orchestrate repo-grounded grilling, specification review, cohesive ticket design, and work-store publication. Use when planning a feature, refactor, migration, or system change into a decision-complete parent plan and executable tasks through BRUTAL.md integrations.
---

# Brutal Plan

Drive planning through explicit stage gates, then publish the approved plan and
tasks through the work store configured in `BRUTAL.md`. Keep the analysis rigorous
and the user-facing checkpoints compact.

## Required Context

1. Read `../brutal-shared/integration-resolver.md`, resolve the work store, and
   load its support module.
2. Read `../brutal-grill/SKILL.md`, `../brutal-spec/SKILL.md`, and
   `../brutal-tickets/SKILL.md`.
3. Read repository rules from `AGENTS.md`, `CLAUDE.md`, `TARGET.md`, and their
   referenced workflow documents.
4. If a completed investigation map is supplied, read its decisions and assets
   and retain a link to it in the specification.

## Choose The Route

Use the normal route when material requirements and design decisions can be
resolved in the current planning conversation. Read
`../brutal-wayfinder/SKILL.md` and offer that route when a necessary decision
depends on separate research, a prototype, unavailable access, or more than one
planning session. Explain the reason and confirm the route before persisting an
investigation map.

## Run The Gates

1. Apply `brutal-grill` until its requirements brief is decision-complete.
2. Apply `brutal-spec`, resolve every validated `PLAN BLOCKER`, and present a
   compact gate-one summary: outcome, scope, key decisions, material risks, and
   acceptance criteria. Obtain explicit approval. Show the full specification
   only when the user asks for it.
3. Apply `brutal-tickets` and present a compact gate-two graph with one line per
   cohesive scope: delivered outcome and genuine blockers. Obtain explicit
   approval of scope boundaries, granularity, blocking edges, and coverage.
   Show complete ticket bodies only when the user asks for them.
4. Publish only after both gates pass. A rejection or unresolved decision leaves
   all work-store artifacts and domain documents unchanged.

## Publish Resumably

Use these markers for normal plan and task dedupe:

```markdown
Source: brutal-plan
Legacy sources: brutal-plan, linear-brutal-plan, gitlear-brutal-plan
```

Before each write, search by source, parent, and exact title. Create or update
the parent and approved glossary or ADR changes before exposing implementation
tasks. Stage complete child bodies in blocker-first order, wire relationships,
update the parent with final identifiers, then promote the children into the
intake queue. If publication fails, stop, keep unpromoted work outside intake,
report every completed and missing write, and resume from that inventory.

The parent body contains the approved specification, completed-map reference if
any, child graph, plan-level acceptance criteria, and known risks. Every child
body follows the `brutal-tickets` contract and mirrors its parent and blockers
even when native relationships exist.

Publish through the resolved work-store contract. Create/update the plan parent
before exposing children, use the adapter's native staging state or its
prepare-before-create strategy, create complete children blocker-first, wire
native relationships where supported, and mirror every parent/blocker in the
body. A remote adapter never creates local work-store artifacts; local
resumable state is allowed only where its support module specifies it.

## Final Response

Report the work store and parent artifact, list each task in dependency order on
one line, name the material risk or partial failure if one exists, and identify
the next unblocked task. Link to persisted detail instead of repeating it.
