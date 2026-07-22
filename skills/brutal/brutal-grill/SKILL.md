---
name: brutal-grill
description: Repo-grounded requirements interrogation that resolves related planning decisions in batched rounds. Use when a feature, refactor, or system change still has material product or engineering choices, or when another Brutal planning skill needs a decision-complete requirements brief.
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
5. When the affected module is opted into Dot Spec, read
   `../brutal-shared/dot-spec-contract.md`, validate its active spec, and
   separate provenance, authority, maturity, and proposal state.

## Grill In Decision Rounds

Ask every currently known, relevant, independent question in one round. Two
questions are independent only when neither answer can change the other's
necessity, wording, or options. After each response, investigate newly exposed
branches and batch the questions they make necessary. Ask nothing when
repository evidence resolves every decision.

Use structured user input when it is available, the whole round has at most
three questions, and each question has 2-3 mutually exclusive options. If the
tool is unavailable or the round does not fit, use one numbered questionnaire
and request a compact reply such as `1B 2A 3: custom answer`.

For each decision question:

- give only the minimum repository evidence that makes it necessary
- offer meaningful options with one-line tradeoffs
- recommend one option in one line

Give a default or example, not an invented recommendation, for genuinely
open-ended input. Keep planning questions separate from caller-owned final
approval, write permission, and safety or model-fallback consent.

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
- for opted-in modules: stable requirement ids, authority per concern,
  provenance and evidence, compatibility classification, base-spec identity,
  intended semantic operations, activation boundaries, and independent
  verification seams

Skip categories that have no bearing on the work. Never turn the list into a
generic questionnaire. Resolve low-impact choices from repository precedent and
record the assumption; ask only when the choice materially changes behavior,
scope, risk, compatibility, or delivery.

## Return A Requirements Brief

Return a compact brief of confirmed requirements, boundaries, invariants,
constraints, assumptions, acceptance scenarios, and unresolved decisions.
Reference evidence instead of repeating the investigation or conversation.
Mark the brief decision-complete only when every high-impact branch is resolved
and the repository evidence agrees with it.

For Dot Spec adoption, never treat observed behavior as desired behavior or
place `unknown` in an active normative spec. Return unresolved evidence through
`brutal-observe` or `brutal-wayfinder` instead of disguising it as an assumption.

Do not persist planning artifacts or edit glossary and ADR files. Pass proposed
domain-language or architectural changes to `brutal-spec` for approval.
