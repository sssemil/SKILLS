---
name: brutal-plan
description: Orchestrate repo-grounded grilling, specification review, tracer-bullet ticket design, and backend publication. Use when planning a feature, refactor, migration, or system change into a decision-complete parent plan and executable tasks in the repo's BRUTAL.md backend.
---

# Brutal Plan

Drive planning through explicit stage gates, then publish the approved plan and
tasks through the backend configured in `BRUTAL.md`.

## Required Context

1. Read `../brutal-shared/backend-resolver.md` and resolve the backend.
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
2. Apply `brutal-spec`, resolve every validated `PLAN BLOCKER`, and obtain
   explicit approval of the complete specification. This is gate one.
3. Apply `brutal-tickets` and obtain explicit approval of the complete ticket
   bodies, acceptance coverage, granularity, and blocker edges. This is gate
   two.
4. Publish only after both gates pass. A rejection or unresolved decision leaves
   all backend artifacts and domain documents unchanged.

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

Persist by backend:

- `local`: write `<local.root>/plans/PLAN-<NNNN>-<slug>.md`; build children under
  `<local.root>/tasks/staged/<plan-slug>/`, then move their complete directories
  to `<local.root>/tasks/todo/` only after every child is ready.
- `linear`: create/update the project document and parent `type:plan` issue;
  stage child `type:task` issues in `Backlog`, wire supported parent and blocker
  links, then promote every child to `Todo`.
- `gitlear`: create/update the project document and parent `type:plan` issue
  before creating child `type:task` issues blocker-first in `todo`. Because
  current Gitlear tools expose neither relationship mutations nor a staging
  state, every created child must have a complete body and all blockers already
  present; mirror relationships in bodies.

Remote backends never create local `<local.root>` planning artifacts.

## Final Response

Report the backend, parent artifact, tasks in dependency order, applied domain
documentation changes, key decisions, known risks, partial failures, and the
next unblocked task.
