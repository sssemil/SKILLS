---
name: brutal-rebuild-audit
description: Prove that a managed Dot Spec module can be reconstructed without seeing its previous implementation. Use for clean-room regeneration, managed-to-rebuildable maturity promotion, generator reproducibility audits, semantic parity checks, or investigating whether code is genuinely disposable rather than merely rewritable with the original present.
---

# Brutal Rebuild Audit

Test reconstructibility without deleting or hiding the user's real working
copy. Produce evidence for a maturity decision; never promote automatically.

## Required Context

1. Read `../brutal-shared/dot-spec-contract.md` and validate the active manifest,
   graph, trace, and module spec.
2. Require module maturity `managed`, a complete generator command, pinned
   declared inputs and toolchain policy, and an independent verification
   command.
3. Read applicable repository build, test, compatibility, data, benchmark, and
   deployment rules.
4. Resolve the exact Git snapshot and canonical normalized spec digests.

## Hard Rules

- Never remove, rename, or conceal the implementation in the user's primary
  worktree. Use a fresh temporary clone or isolated worktree.
- The generator may read only accepted module specifications, imported
  contracts, approved policies, locked architecture decisions, and declared
  foreign dependencies.
- Do not expose the old implementation through Git history, build caches,
  generated artifacts, search indexes, prompts, or copied tests that encode its
  internal structure.
- Compare semantic obligations, not source-text similarity.
- Fail on undeclared inputs, network dependencies outside policy, stale specs,
  verification gaps, or parity failures. Never weaken the spec to pass.

## Run The Clean-Room Audit

1. Create an isolated checkout at the recorded snapshot and a separate audit
   output directory.
2. Remove the target implementation only inside the isolated copy. Preserve
   public contracts and independent verification surfaces; exclude tests that
   merely mirror private implementation structure.
3. Clear or redirect relevant caches. Record generator version, model and prompt
   policy when applicable, dependency locks, environment, commands, and inputs.
4. Generate the complete bounded module from declared inputs only.
5. Run ordinary compilation and toolchain checks, then the independently
   configured verification command.
6. Compare observable interfaces, scenarios, invariants, compatibility, data
   behavior, external effects, performance constraints, and operational rules.
7. Run the build again from a fresh output directory when deterministic output
   is claimed. Treat textual differences as diagnostic unless textual identity
   is itself a declared requirement.

## Decide Rebuildability

Recommend `managed -> rebuildable` only when:

- the complete implementation was inaccessible during generation
- every declared input was recorded and permitted
- all active requirements have independent passing evidence
- compatibility and data obligations pass
- no material behavior depends on the hidden implementation
- repeated runs satisfy the repository's reproducibility policy

Promotion must be an approved semantic change merged with its audit evidence.
Otherwise retain `managed` and report the smallest missing knowledge or control.

## Audit Record

Return the repository/module snapshot, spec and generator digests, isolation
method, declared inputs, environment policy, commands, semantic results,
textual-difference diagnostics, failures, retained artifacts, and promotion
recommendation. Never describe a rewrite performed with access to the old code
as a clean-room rebuild.
