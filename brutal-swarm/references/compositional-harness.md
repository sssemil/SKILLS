# Compositional Harness Contract

Use this contract when planning or executing a coordinated Brutal graph. Keep
bulk context in artifacts and give each fresh worker only its task capsule and
phase projection.

## Coordination Domains

Every new ticket defines:

```yaml
decisions_owned:
  - id: api.shape
    statement: Responses use the v2 envelope.
decisions_consumed:
  - storage.layout
touch_surfaces:
  - path: src/api
    kind: prefix # file | prefix
    parallel_safe: false
```

Use stable lowercase decision IDs matching `[a-z0-9][a-z0-9._-]*`. Give each
decision exactly one owner. Put approved statements in the plan-scoped,
immutable decision registry. A consumer may start only when the registry or a
blocking ancestor owns every consumed decision.

Normalize touch paths as repository-relative POSIX paths. Serialize overlapping
file/prefix surfaces in scheduler order unless both declarations set
`parallel_safe: true`. Allow legacy tickets without these fields, but report
them as `coordination_unscoped`.

## Task Capsule V1

Build one immutable capsule containing only:

- task ref, kind, title, goal, acceptance criteria, and blockers;
- the three coordination domains;
- exact verification commands;
- content-addressed artifact references.

Every artifact reference is exactly `{path, sha256, bytes, media_type}`. Resolve
the path inside the run root and validate size and SHA-256 before reading it.

## Managed Context V3

New managed launches use manifest v3. Retained v1/v2 runs continue unchanged;
never migrate them automatically. Store raw ticket, provider, diff, checks,
logs, review queues, and outputs as artifacts. A phase prompt contains only the
phase, manifest path, manifest digest, and validation/result instruction. Keep
it at or below 2 KiB. Every v3 result echoes the exact `context_digest`.

Use these phase projections:

| Phase | Allowed context |
|---|---|
| `work` | capsule, decision projection, repository rules, Field Guide projection |
| `review` | acceptance/diff/code/check projections separated by review lens |
| `fix` | exact generated finding-occurrence queue plus current snapshot |
| `reconcile` | conflict manifest and governing decisions |
| `handoff` / `complete` | checkpoint and provider summaries |

Reject stale digests, path escapes, missing artifacts, or unexpected projection
fields. Write mutable JSON atomically; keep content-addressed artifacts
immutable.

## Field Guide

Persist one repository Field Guide across runs. Store repository facts only,
not task progress or product decisions. A worker may propose at most five facts
per phase, each with repository path and current Git blob SHA evidence. The
controller alone merges proposals, deduplicates by ID, excludes stale evidence,
and evicts least-recently-used entries deterministically.

Limit the stored guide to 12 KiB and 120 rendered lines. Give a phase only a
touch/tag-relevant projection of at most 2 KiB.

## Decorrelated Review Lenses

Give reviewer threads different evidence rather than the same bundle with a
different label:

- product: acceptance criteria and diff summary;
- correctness: diff, relevant code, and callers;
- reliability: tests, checks, and failure summaries;
- security/performance: exposed surfaces, concurrency, and resource summary;
- simplicity: diff and repository style only.

Store raw analyses as artifacts. Merge only validated structured findings.

## Neutral Reconciliation

When `work` or `fix` encounters a merge/rebase conflict, return a conflict
manifest and stop. The controller starts a fresh `reconcile` thread with no
worker transcript. It may perform only a mechanical resolution consistent with
the immutable decision registry, create a local merge commit, and run focused
verification. It never pushes or makes a product decision.

On success, return to the originating `work` or `fix` phase, which revalidates
and publishes. If the conflict is semantic, return `blocked` and preserve the
conflict artifact and worktree.
