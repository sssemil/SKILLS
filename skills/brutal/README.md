# Brutal skills

The brutal-\* family is based on this article - https://readyset.io/blog/brutal-review-and-the-new-80-20-rule

The Brutal planning, project review, worker, swarm, and pull-request review skills
use a repo-local `BRUTAL.md` file to resolve one code host and one work store.
Built-in support covers GitHub plus local files, Linear, Gitlear, and Jira;
complete custom adapters can be described in the file. See
[`brutal-shared/BRUTAL.example.md`](brutal-shared/BRUTAL.example.md) for the
canonical shape. Legacy version-1 backend files and unambiguous prose remain
supported.

## Brutal workflow map

```text
+====================================================================================+
|                              BRUTAL.md CONTROL PLANE                               |
|                                                                                    |
|  code host: GitHub        work store: local | Linear | Gitlear | Jira              |
|  workers: tmux (default) | native subagents        rules + verification: repo docs |
+=========================================+==========================================+
                                          |
              +---------------------------+---------------------------+
              |                                                       |
              v                                                       v
  +-------------------------+                              +-------------------------+
  |     IDEA / RESEARCH     |                              |    FEATURE / REFACTOR   |
  +-------------------------+                              +-------------------------+
              |                                                           |
              v                                                           |
  +-------------------------+                                             |
  | brutal-idea-eval        |                                             |
  |                         |                                             |
  | + brutal-reality        |                                             |
  | + brutal-deepresearch   |                                             |
  | + revenue / VC filters  |                                             |
  +------------+------------+                                             |
               | verdict / pivot                                          |
               +---------------------------+-------------------------------+
                                           |
                      fog, prototypes,      | decision-ready work
                      access, research      |
                              |             |
                              v             v
                     +----------------+  +----------------+
                     | brutal-        |  | brutal-plan    |
                     | wayfinder      |->| orchestrator   |
                     +-------+--------+  +-------+--------+
                             |                   |
                             | resolved map      v
                             +----------> [ brutal-grill ]
                                                 |
                                                 v
                                          [ brutal-spec ]
                                                 |
                                        HUMAN APPROVAL GATE
                                                 |
                                                 v
                                        [ brutal-tickets ]
                                                 |
                                        HUMAN APPROVAL GATE
                                                 |
                                                 v
  EXISTING REPO --------> [ brutal-project-review ] ------+
     subsystem audit          CRITICAL / MAJOR tasks       |
                                                           v
                                             +---------------------------+
                                             |   WORK STORE TASK GRAPH   |
                                             +-------------+-------------+
                                                           |
                                                           v
                                             +---------------------------+
                                             |       brutal-swarm        |
                                             | dependency waves + bases  |
                                             | work>review<>fix>handoff  |
                                             | one context.json per phase|
                                             +-------------+-------------+
                                                           |
                           +-------------------------------+------------------+
                           |                               |                  |
                           v                               v                  v
                  +----------------+              +----------------+  +----------------+
                  | brutal-worker  |              | brutal-worker  |  | brutal-worker  |
                  | task A         |              | task B         |  | task N         |
                  | branch/worktree|              | branch/worktree|  | branch/worktree|
                  +-------+--------+              +-------+--------+  +-------+--------+
                          |                               |                   |
                          +-------------------------------+-------------------+
                                                          |
                                                          v
                                             +---------------------------+
                                             |      STACKED PR GRAPH     |
                                             | PR A <- PR B <- PR C      |
                                             | one PR per exact ticket   |
                                             +-------------+-------------+
                                                           |
                                                           v
                                             +---------------------------+
                                             | brutal-inf-fix-loop       |
                                             | uncapped worker default   |
                                             +-------------+-------------+
                                                           |
                                +--------------------------+-------------------+
                                |                                              |
                                v                                              |
                     +--------------------+                                     |
                     | brutal-pr-review   |                                     |
                     +---------+----------+                                     |
                               | generated findings                             |
                               v                                                |
                 +----------------------------+                                 |
                 | brutal-pr-finding-fixer    |---------------------------------+
                 +-------------+--------------+          review again
                               |
                        fresh clean pass
                               v
                         HUMAN MERGE  ------------------------------> task done

  Alternate bounded PR cleanup:
      open PR --> [ brutal-pr-fix-loop: max 3 passes ] --> review + fixer pair

  Local pre-PR sidecar:
      git HEAD / jj @- --> [ brutal-review ] --> ruthless local findings

  Standalone research sidecar:
      research question --> [ brutal-deepresearch ] --> validated report
                                                   --> idea eval / wayfinder / spec
```

Arrows show the normal handoff path. Human approval gates prevent planning from
publishing tasks early, and human merge remains the only path from a clean pull
request to a completed task.

## Brutal planning

The planning workflow is a composable, two-gate suite:

- [`brutal-plan`](brutal-plan/SKILL.md) orchestrates planning and publishes the
  approved parent plan and implementation tasks.
- [`brutal-grill`](brutal-grill/SKILL.md) resolves one repo-grounded decision at
  a time.
- [`brutal-spec`](brutal-spec/SKILL.md) synthesizes and stress-tests the
  decision-complete specification.
- [`brutal-tickets`](brutal-tickets/SKILL.md) produces the fewest cohesive,
  decision-complete implementation scopes.
- [`brutal-wayfinder`](brutal-wayfinder/SKILL.md) persists investigation maps
  for work that needs research, prototypes, access, or multiple planning
  sessions before implementation can be specified.

`brutal-plan` writes nothing until the specification and complete ticket graph
have both been approved. Work-store adapters stage or prepare complete tasks
outside the worker intake queue until publication is ready. Wayfinder maps and
questions use `type:investigation`, so `brutal-worker` cannot select them.

## Opt-in Dot Spec overlay

A repository can add a `dot_spec` section to `BRUTAL.md` and list opted-in
modules in a machine-first manifest. Those modules bind planning, tickets,
workers, reviews, and independent verification to an approved normalized
semantic delta. Approval freezes the delta; the pull request merges canonical
spec, code, tests, trace, and evidence atomically, so `main` never advertises
behavior that has not landed.

The shared contract and deterministic helper live in
[`brutal-shared/dot-spec-contract.md`](brutal-shared/dot-spec-contract.md) and
`brutal-shared/scripts/dotspec.py`. The helper validates module ownership,
authority, provenance, maturity, imports, guards, and approved deltas; it also
normalizes, hashes, semantically diffs, and generates public-seam trace output.

- [`brutal-observe`](brutal-observe/SKILL.md) moves legacy knowledge from
  `code-owned` toward `observed` and `guarded` without canonizing accidents.
- [`brutal-rebuild-audit`](brutal-rebuild-audit/SKILL.md) proves a `managed`
  module can be reconstructed without access to its previous implementation.

Modules absent from the manifest retain ordinary Brutal behavior. The maturity
path is `code-owned -> observed -> guarded -> spec-driven -> managed ->
rebuildable`; every promotion is an approved, evidence-backed semantic change.

## Brutal execution

- [`brutal-worker`](brutal-worker/SKILL.md) owns one exact task through an
  isolated worktree, one stacked pull request, and an uncapped materially clean
  Brutal review/fix loop.
- [`brutal-swarm`](brutal-swarm/SKILL.md) asks for a concurrency cap and drains
  a task graph through parallel workers. It defaults to one retained tmux Codex
  session per task with fresh phase-scoped Codex threads and one small context
  file per phase; `BRUTAL.md` can select native subagents instead. Independent
  roots run side by side, while single-blocker children target stack-ready
  blocker branches until those PRs merge.

## Brutal pull-request loops

- [`brutal-pr-review`](brutal-pr-review/SKILL.md) posts provider-native,
  individually actionable findings for the current open pull request.
- [`brutal-pr-finding-fixer`](brutal-pr-finding-fixer/SKILL.md) fixes generated
  findings one at a time.
- [`brutal-pr-fix-loop`](brutal-pr-fix-loop/SKILL.md) preserves the bounded
  three-pass review/fix behavior.
- [`brutal-inf-fix-loop`](brutal-inf-fix-loop/SKILL.md) repeats without a pass
  or no-progress cap until a fresh all-severity review has no CRITICAL or MAJOR
  findings. A MINOR/NIT-only pass is recorded as materially clean.

This rework adopts the grilling, decision-complete specification,
expand-contract, and fog-of-war ideas from
[Matt Pocock's engineering skills](https://github.com/mattpocock/skills), while
retaining the Brutal `BRUTAL.md` integration model.

brutal-deepresearch is based on [Deep-Research-skills](https://github.com/Weizhena/Deep-Research-skills) by Weizhena.

brutal-reality is based on [Reality's Moat](https://davidbeyer.xyz/writing/realitys-moat) by David Beyer.

## License

See [LICENSE](../../LICENSE).
