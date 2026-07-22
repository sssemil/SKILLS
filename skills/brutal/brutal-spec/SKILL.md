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

Write only the contract an implementer needs. Reuse the requirements brief by
reference instead of restating it, combine related material, and omit sections
that do not change implementation. Use this compact shape:

```markdown
## Outcome And Scope
## Behavior And Boundaries
## Interfaces, Data, And Migration
## Implementation Decisions
## Verification And Acceptance
## Risks, Assumptions, And Domain Documentation
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
and return every simultaneously answerable validated blocker to `brutal-grill`
in one round. Defer a blocker when another answer can change its necessity,
wording, or options; never expose an unvalidated finding as a user question.

## Approval Gate

Present outcome, scope, key decisions, material risks, and acceptance criteria
as the compact approval view. Keep that view to one short paragraph and at most
seven bullets total; group related decisions, risks, and criteria. Show the
complete revised specification only when the user asks for it or the
specification text itself is the requested deliverable. The stage completes
only when the user approves and no `PLAN BLOCKER` or open material decision
remains. Return the approved full specification to the calling skill without
persisting it.
