---
name: brutal-spec
description: Synthesize repo evidence and resolved requirements into a reviewed, decision-complete implementation specification. Use after requirements grilling, when converting a planning conversation or completed investigation map into the parent specification for a Brutal plan.
---

# Brutal Spec

Turn a decision-complete requirements brief into the behavioral and technical
contract that implementation tickets will inherit. Do not publish artifacts.

## Verify The Inputs

Read the requirements brief, relevant repository instructions, domain glossary,
ADRs, affected interfaces, tests, and any linked research, prototype, or
completed investigation map. Return unresolved material decisions to
`brutal-grill`; do not hide them as assumptions.

## Draft The Specification

Use this shape, omitting only sections that genuinely do not apply:

```markdown
## Problem And Outcome
## Actors And Behavior Scenarios
## Scope And Anti-Goals
## Interfaces, Data, And Compatibility
## Implementation Decisions And Rationale
## Testing Seams And Verification
## Migration, Rollout, And Observability
## Invariants And Acceptance Criteria
## Risks And Assumptions
## Proposed Domain Documentation
```

State public interface, schema, migration, and wire-format changes precisely.
Prefer stable module and domain names over file paths. Include a code or type
snippet only when a prototype established a decision more precisely than prose.

Choose the highest existing public seams that can verify the behavior. Keep the
number of seams small, explain any new seam, and name exact repository commands
that will verify the finished work.

Propose a glossary edit when planning resolves domain language. Propose an ADR
only when the decision is hard to reverse, surprising without context, and the
result of a genuine tradeoff. Do not edit either document yet.

## Stress-Test The Draft

When independent reviewers are available, review the same draft and evidence
from these perspectives:

- architecture, module depth, and coupling
- data model, compatibility, and migration safety
- public interface, UX, and integration behavior
- reliability, security, operations, and delivery risk

Classify findings as `PLAN BLOCKER`, `IMPLEMENTATION NOTE`, or `SUGGESTION`.
Validate each finding against the repository, fold valid notes into the draft,
and return every blocker to `brutal-grill` one decision at a time.

## Approval Gate

Present the complete revised specification, including proposed glossary and ADR
changes, and request explicit approval. The stage completes only when the user
approves the specification and no `PLAN BLOCKER` or open material decision
remains. Return the approved specification without persisting it.
