---
name: brutal-wayfinder
description: Map and resolve planning work whose route is still hidden by research, prototypes, access, or decisions spanning multiple sessions. Use for large or foggy efforts that cannot yet produce a decision-complete Brutal specification and implementation tickets.
---

# Brutal Wayfinder

Persist a resumable map of questions until the route to a decision-complete
specification is clear. Produce planning decisions, not destination
implementation.

## Required Context

1. Read `../brutal-shared/backend-resolver.md` and resolve the backend.
2. Read `../brutal-grill/SKILL.md`.
3. Read repository instructions, domain context, ADRs, and existing map state.
4. Use `type:investigation` for every map and investigation ticket. These
   artifacts never enter the implementation task queue.

## Map Contract

Use `Source: brutal-wayfinder`. A map contains:

```markdown
## Destination
## Notes
## Decisions So Far
## Not Yet Specified
## Out Of Scope
```

The destination states what must exist when wayfinding ends. `Decisions So Far`
is an index of resolved ticket names and one-line outcomes, not a duplicate of
their full resolutions. `Not Yet Specified` holds in-scope fog that cannot yet
be phrased as a precise question.

Each child ticket contains its parent, one precise `Question`, blockers, claim,
status, and one mode:

- `research` — agent-only primary-source investigation
- `prototype` — human-in-the-loop artifact for behavior or design feedback
- `grilling` — human-in-the-loop decision using `brutal-grill`
- `task` — prerequisite work needed to expose facts for a later decision

A prerequisite task must unblock a planning decision; destination implementation
belongs in the later Brutal plan.

## Chart A Map

1. Use `brutal-grill` to name and confirm the destination.
2. Map breadth-first: identify precise questions that can be ticketed now and
   record the remaining fog without prematurely slicing it.
3. If no fog remains and the decisions fit the current planning conversation,
   return to `brutal-plan` without creating a map.
4. Present the destination, initial tickets, blockers, and fog. Publish only
   after explicit approval.
5. Create the map first, then child tickets, then native relationships where
   supported. Mirror parent and blocker references in every ticket body.

Persist local maps at
`<local.root>/investigations/<NNNN>-<slug>/map.md` and tickets under
`tickets/{todo,in-progress,done}/<NN>-<slug>.md`. For Linear and Gitlear, use a
parent issue and child issues in the resolved project. Never create local
investigation files for a remote backend.

## Work A Map

1. Load the map as the low-resolution index and query open children.
2. Identify the frontier: open, unblocked, unclaimed tickets.
3. Ask whether this run should resolve one frontier question or continue through
   ready agent-only questions.
4. Claim a ticket before work. In continuous mode, pause before any
   human-in-the-loop ticket.
5. Record the full resolution on the ticket, mark it done, and append its linked
   one-line outcome to `Decisions So Far`.
6. Add newly visible questions, graduate sharpened fog into tickets, and move
   newly excluded work to `Out Of Scope`.

Use backend-native assignment, statuses, comments, parents, and blockers when
available; preserve the same information in bodies when they are not.

Complete the map only when no open ticket or fog remains. Mark the parent done
and hand its reference to `brutal-plan`, which consumes the decisions, proposes
any domain-document changes, and links the map from the final specification.

On rerun, deduplicate by `Source`, parent reference, and exact ticket title.
Report partial publication or update failures precisely so the next run can
resume rather than duplicate artifacts.
