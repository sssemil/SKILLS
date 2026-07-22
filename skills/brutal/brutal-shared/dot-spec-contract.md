# Brutal Dot Spec Contract

Use this contract only when `BRUTAL.md` contains a `dot_spec` section and the
affected module is listed in its manifest. Modules that are not listed keep the
ordinary Brutal workflow.

## Configuration

Resolve these `BRUTAL.md` values without guessing:

```yaml
dot_spec:
  manifest: .dotspec/modules.yaml
  command: dotspec
  independent_verify: ./scripts/verify-contracts
```

- `manifest` is repository-relative and identifies every opted-in module.
- `command` provides `validate`, `normalize`, `digest`, `diff`, `trace`, and
  `verify`.
- `independent_verify` checks public behavior independently of worker-authored
  implementation tests. It is required for `guarded` and later modules.

Validate the manifest and command before planning or implementing an opted-in
module. Never silently disable Dot Spec because configuration or validation is
broken.

## Active Module Manifest

Use a machine-first YAML or JSON manifest:

```yaml
schema_version: 1
modules:
  - id: billing
    spec: modules/billing.spec.yaml
    maturity: guarded
    authority:
      behavior: spec
      implementation: code
      tax_rules: foreign
```

Module ids are unique. `spec` paths are relative to the manifest. Authority is
singular per concern and accepts only `spec`, `code`, or `foreign`.
The version-1 helper rejects manifest membership changes during semantic diff;
enroll or retire a module through a separately reviewed governance change.

Maturity advances deliberately:

```text
code-owned -> observed -> guarded -> spec-driven -> managed -> rebuildable
```

Do not infer maturity from file presence. Promotion requires evidence for the
new stage and an approved semantic change.

## Canonical Module Specification

An active specification contains only accepted behavior:

```yaml
schema_version: 1
module: billing
imports:
  - module: identity
seams:
  - public-api
requirements:
  - id: billing.invoice-idempotency
    concern: behavior
    statement: Repeating an invoice request with the same key has one effect.
    provenance:
      kind: declared
      refs:
        - ADR-0042
    scenarios:
      - id: billing.invoice-idempotency.retry
        given: A completed request and the same idempotency key
        when: The client repeats the request
        then: The original result is returned without another charge
    invariants:
      - id: billing.invoice-idempotency.single-charge
        statement: One idempotency key creates at most one charge.
    seams:
      - public-api
    verification:
      - contract-tests::invoice_idempotency
```

Requirement ids are immutable and globally unique. Each requirement has one
owning module and one authority concern. Imports are repository-local,
read-only, acyclic references resolved at the same Git snapshot.

Provenance accepts `declared`, `observed`, `asserted`, or `inferred` in active
specifications. Preserve `unknown` only in investigation or proposal artifacts;
never activate it as a normative requirement. Provenance records evidence and
does not grant authority.

Implementation freedom is descriptive unless expressed as an observable
boundary, prohibition, scenario, invariant, or verification obligation.

## Approved Semantic Change

Approval freezes an immutable semantic change contract; it does not update the
active specification on the default branch.

```yaml
schema_version: 1
change_id: dot-2026-0042
base_sha: <git sha>
base_specs:
  billing: <normalized spec sha256>
approval:
  status: approved
  by: <stable identity>
  at: <RFC3339 timestamp>
operations:
  - op: replace
    module: billing
    requirement_id: billing.invoice-idempotency
    ticket: billing-idempotency
    activates_with: billing-idempotency
    before_digest: <normalized requirement sha256>
    after:
      <complete replacement requirement>
module_changes:
  - module: billing
    ticket: billing-idempotency
    activates_with: billing-idempotency
    before_digest: <normalized maturity/authority/import/seam sha256>
    after:
      maturity: spec-driven
      authority:
        behavior: spec
        implementation: code
      imports:
        - module: identity
      seams:
        - public-api
```

Operations are `add`, `replace`, or `remove`. Module changes cover maturity,
authority, imports, and default public seams. In an approved delta, `ticket`
and `activates_with` are stable logical scope keys selected before provider
artifacts exist. Each operation belongs to one logical ticket scope and one
activation scope. Gate two maps those keys to approved ticket boundaries.
Publication and worker handoff bind provider ticket and pull-request refs in
task metadata outside the normalized semantic delta, so those refs never
change its digest. A cross-ticket requirement remains proposed until its final
activating scope merges. Bind every ticket and worker handoff to the change id,
normalized delta digest, base SHA, and applicable base-spec digests.

Workers may implement only the assigned operations. Any different semantic
change, authority change, compatibility decision, or acceptance weakening
returns to planning and approval. Strengthening internal tests is allowed only
when it does not narrow public behavior beyond the accepted contract.

The pull request that activates an operation updates the canonical spec, code,
tests, and evidence atomically. Merge is the activation event.

## Trace And Independent Evidence

Generate trace output; never hand-edit it. Trace each requirement to:

- owning module and authority concern
- approved change and ticket when applicable
- public seams
- scenarios and invariants
- verification identifiers and independent check evidence
- activating commit after merge

Start with module and public-seam traceability. Require symbol- or line-level
annotations only when a repository has a stable existing convention.

Independent verification is not another agent repeating worker-authored tests.
Use an independently configured command over public seams, existing contracts,
schemas, characterization tests, static policies, benchmarks, or external
conformance suites. Key evidence by complete base/head snapshot and normalized
spec digest.

Run a verifier without a shell and persist its evidence, for example:

```text
dotspec verify .dotspec/modules.yaml --head-sha <sha> \
  --output <evidence.json> -- ./scripts/verify-contracts
```

Verification resolves the repository root from the manifest, requires the
declared SHA to equal a clean `HEAD` before and after the command, and runs the
command from that root.

## Failure Rules

Fail before mutation or publication when:

- ids, owners, authorities, or imports are invalid or ambiguous
- the approved base SHA or spec digest is stale
- the actual semantic diff differs from approved operations
- an activated guarded requirement lacks mandatory evidence
- a worker or finding fixer weakens a contract outside the approved delta
- a maturity promotion lacks its required evidence

Do not repair these failures by weakening the specification, deleting a hard
scenario, broadening an assumption, or silently returning the module to ordinary
Brutal behavior.
