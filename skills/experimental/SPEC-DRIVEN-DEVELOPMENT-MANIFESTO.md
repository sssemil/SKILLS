# The Dot Spec Manifesto

## Specification-Driven Development

Software has treated source code as the enduring expression of a system and
everything else as supporting material. Dot Spec proposes a different order:

> **The specification is the source. Code is a build artifact. A coding agent is
> a compiler backend.**

We should commit the behavior, boundaries, constraints, and intent of a system.
Implementations should increasingly be derived from that record, verified by
ordinary toolchains, and replaceable without losing what the system means.

This is not a claim that today's code can be discarded. Existing implementations
contain years of implicit knowledge: edge cases, compatibility obligations,
operational assumptions, and accidental behavior that users may now depend on.
Reconstructibility must be earned. Dot Spec therefore joins a radical destination
to a pragmatic path: preserve today's systems while progressively transferring
authority from code to specifications.

## What We Mean by a Specification

A Dot Spec is not a prompt that asks an agent to “build something secure.” It is
not polished documentation that drifts away from the product. It is a structured,
versioned behavioral contract.

It records, where relevant:

- Purpose and responsibility
- Public interfaces and compatibility boundaries
- Observable behavior and failure modes
- Invariants and measurable constraints
- Scenarios and acceptance criteria
- Dependencies and external effects
- Architecture decisions and permitted implementation freedom
- Non-goals, conflicts, unknowns, and supporting evidence

Natural language remains useful, but consequential ambiguity is a compilation
error. Requirements must be precise enough to verify. When intent cannot be
determined safely, the specification must preserve the uncertainty instead of
allowing an agent to disguise a guess as a decision.

## What We Value

### Intent over implementation

Implementation matters, but it is not the most durable description of why a
system exists or what it must do. Git should preserve reviewed intent so that a
new implementation can recover the same obligations.

### Executable contracts over suggestive documentation

Documentation explains. A specification also constrains, generates, rejects,
and verifies. Its interfaces, scenarios, and invariants must have operational
meaning.

### Evidence over inference

Existing code can reveal behavior, but it cannot always reveal intent. Tests,
schemas, documentation, runtime observations, and implementation details are
different kinds of evidence. Dot Spec names the difference instead of flattening
them into confident prose.

### Explicit authority over bidirectional ambiguity

Code and specification must not both silently claim the same decision. For each
concern—contract, behavior, or implementation—the repository must say which side
is authoritative. Reconciliation is a deliberate act, not background
synchronization.

### Independent verification over self-validation

An agent that writes both an implementation and every test can repeat the same
misunderstanding twice. Verification must be derived from multiple independent
surfaces: contracts, declared scenarios, invariants, legacy characterization,
policies, static analysis, benchmarks, and existing toolchains.

### Semantic stability over textual similarity

The important question is not whether regenerated files have identical lines. It
is whether the system preserves its observable contracts, invariants, data, and
operational behavior. Textual reproducibility is valuable; semantic
reproducibility is essential.

## Principles

1. **Specifications preserve intent.** Meaningful product and engineering
   decisions belong in durable, reviewable repository artifacts rather than
   transient conversations.

2. **Consequential ambiguity must stop the build.** A compiler may choose local
   implementation details, but it must not invent security policy, compatibility
   behavior, data semantics, or other product decisions.

3. **Provenance is part of meaning.** Every consequential statement must be
   identified as declared, observed, asserted, inferred, or unknown. Confidence
   must never substitute for evidence.

4. **Authority is explicit and singular.** Each concern has one source of truth:
   code, specification, or a declared foreign dependency. Authority changes only
   through an intentional, reviewable transition.

5. **Adoption begins without a rewrite.** A repository may start entirely
   code-owned. Initial specifications describe and guard the existing system
   while its ordinary build, review, debugging, and deployment practices remain
   intact.

6. **Observed behavior is not automatically desired behavior.** Decompilation
   produces candidate specifications, evidence, conflicts, and unknowns. It must
   not canonize every implementation accident as a requirement.

7. **Changes are reviewed semantically.** A useful change report explains which
   contracts, behaviors, invariants, and constraints changed—not only which lines
   changed.

8. **Requirements remain traceable.** A developer must be able to follow a
   requirement to the implementation that realizes it and to the checks that
   verify it, then trace an artifact back to the intent that required it.

9. **Compilation must fail honestly.** When an implementation cannot satisfy the
   accepted specification, the system must fail rather than weaken a requirement,
   remove a difficult scenario, or quietly broaden an assumption.

10. **Architecture evolves deliberately.** Compiler-selected decisions are
    recorded and preserved across ordinary builds. Replanning, dependency
    upgrades, and architectural change are explicit evolution operations, not
    incidental consequences of regeneration.

11. **Compilation units stay bounded.** A module should compile from its own
    specification, imported contracts, approved policies, and locked decisions.
    This makes builds incremental, cacheable, parallel, and increasingly cheap to
    run with local models and deterministic generators.

12. **Rebuildability must be proven.** Code is not disposable merely because an
    agent can rewrite it while reading the original. A clean rebuild hides the
    previous implementation and reconstructs the module only from accepted
    specifications and declared dependencies.

## The Transition

Specification-driven development is a transfer of authority, not a flag day:

```text
code-owned → observed → guarded → spec-driven → managed → rebuildable
```

**Code-owned** systems work as they do today. Code remains authoritative.

**Observed** systems have evidence-backed candidate specifications that expose
behavior, conflicts, and unknowns.

**Guarded** systems enforce accepted contracts and invariants while developers
continue to write their implementations directly.

**Spec-driven** systems begin changes from an accepted semantic delta. Agents
produce focused implementation patches that humans review through normal source
control and continuous integration.

**Managed** systems regenerate complete modules from specifications while
preserving declared architecture decisions and foreign boundaries.

**Rebuildable** systems pass clean-room regeneration and compatibility checks.
Their implementation is genuinely replaceable because the knowledge needed to
recover it no longer exists only in the code.

A single repository may contain modules at every stage. Progress is measured by
captured intent, verified behavior, explicit authority, and clean-room parity—not
by how much code an agent has generated.

## The Standard

A module is truly Dot-Spec-driven when its implementation can be hidden or
deleted, regenerated from accepted specifications and declared dependencies, and
still satisfy its contracts, invariants, compatibility obligations, and
independent verification.

Until then, its code remains valuable evidence. The path forward is not to deny
that value, but to extract it, examine it, resolve it, and make it reproducible.

Dot Spec exists to make that transition possible:

> **Git stores intent. Code is compiled from it.**
