---
name: brutal-grill
description: Repo-grounded requirements interrogation that resolves one planning decision at a time. Use when a feature, refactor, or system change still has material product or engineering choices, or when another Brutal planning skill needs a decision-complete requirements brief.
---

# Brutal Grill

Resolve every material planning decision without asking the user for facts the
repository can supply.

## Ground The Discussion

1. Read applicable `AGENTS.md`, `CLAUDE.md`, `TARGET.md`, and referenced workflow
   documents.
2. Read `CONTEXT.md` or the relevant entry from `CONTEXT-MAP.md`, plus ADRs in
   the affected area. Use their domain language and surface contradictions.
3. Inspect affected modules, callers, schemas, migrations, interfaces, tests,
   and prior art with `rg` and `rg --files`.
4. Separate discoverable facts from decisions. Investigate facts; ask only for
   decisions.

## Grill One Decision At A Time

Ask exactly one question, wait for the answer, then follow the branch it opens.
For each question:

- cite the repository evidence or prior answer that makes it necessary
- offer meaningful options and their tradeoffs
- recommend one option and explain why
- use the user-input tool when available

Resolve contradictions immediately. Prefer concrete scenarios, payloads, state
transitions, failure examples, and boundary values over abstract questions.
Continue until the brief covers:

- goal, actors, and observable behavior
- inputs, outputs, interfaces, and compatibility constraints
- scope, anti-goals, and existing behavior that must remain stable
- empty, invalid, partial-failure, concurrency, and dependency-failure behavior
- security, privacy, performance, observability, migration, and rollout where
  relevant
- acceptance scenarios and 1-3 invariants

Skip categories that have no bearing on the work. Never turn the list into a
generic questionnaire.

## Return A Requirements Brief

Return confirmed requirements, scope boundaries, anti-goals, invariants,
constraints, assumptions, acceptance scenarios, and any unresolved decisions.
Mark the brief decision-complete only when every high-impact branch is resolved
and the repository evidence agrees with it.

Do not persist planning artifacts or edit glossary and ADR files. Pass proposed
domain-language or architectural changes to `brutal-spec` for approval.
