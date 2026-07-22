# Parallel Execution Contract

Read this reference before scheduling a Brutal Swarm run.

## Immutable Assignment Handoff

Pass one exact assignment to each worker:

```yaml
mode: managed
run_id: <safe unique token>
task_ref: <stable provider ref>
task_kind: task | review_finding
worker_runtime: tmux | subagent
phase: work | review | fix | complete
runtime:
  session_name: <tmux session or null>
  state_dir: <absolute tmux state directory or null>
work_store:
  adapter: <name>
  identity: <workspace/project identity>
  canonical_local_root: <absolute path or null>
code_host:
  adapter: <name>
  repository: <stable repository identity>
worktree_path: <absolute path>
branch: <task branch>
branch_head: <sha>
base_branch: <remote branch>
base_sha: <sha>
task_state: <normalized state>
task_owner: <stable owner or null>
pull_request: <provider identity or null>
checks: <normalized check state or null>
stacked_on:
  task_ref: <single blocker ref or null>
  pr: <provider PR ref or null>
dot_spec:
  change_id: <stable id or null>
  delta_digest: <normalized sha256 or null>
  base_specs: <module-to-digest mapping>
  operations: <exact ticket-owned operations>
  activates: <requirement ids activated by this PR>
  independent_verify: <validated command or null>
```

Assignment identity is immutable. The runtime adapter fills its runtime fields
before launch. Runtime data grants no task, Git, or provider authority.

## Context File

Keep bulk phase input in one run-local `context.json`. The prompt contains only
phase, context path, and result path, and must stay below 2 KiB.

- `work`: ticket, repository rules, branch state
- `review`: acceptance criteria, diff/relevant code, checks
- `fix`: exact finding queue
- `handoff`: final verification and provider state

Dot Spec assignment values are immutable. Mutable snapshots may report current
actual spec/delta digests and verification evidence but never replace the
approved assignment.

## Mutable Phase Snapshot

Before every managed phase transition, re-read live provider and Git state and
write a schema-versioned snapshot containing:

```yaml
schema_version: 1
identity:
  task_ref: <exact assignment ref>
  branch: <exact branch>
  worktree_path: <exact path>
  code_host_repository: <exact repository identity>
live:
  task_state: <current state>
  task_owner: <current owner>
  branch_head: <current local/provider head>
  base_branch: <current PR base branch>
  base_sha: <current base SHA>
  pull_request: <current identity and state>
  checks: <current normalized checks>
```

The immutable handoff says *what is owned*; the phase snapshot says *what is
true now*. Reject identity mismatches rather than silently adopting new work.
Review evidence is keyed by the complete base/head snapshot, never head alone.

## Managed Worker Protocol

`tmux_worker.py` stores `attempts/000001`, `000002`, … and an atomic
`active.json`. Each attempt owns its prompt, phase snapshot, result schema,
events, result, and exit record. Attempts are append-only.

| Phase | Worker scope | Successful result | Controller successor |
| --- | --- | --- | --- |
| `work` | claim, implement, verify, publish PR | checkpoint | `review` |
| `review` | one fresh material-convergence review | checkpoint | `fix` if CRITICAL+MAJOR > 0; else `handoff` |
| `fix` | drain that review’s full queue, verify, push | checkpoint | `review` |
| `handoff` | final revalidation and task transition | terminal clean | none |
| `complete` | record an already-merged PR and close task | terminal merged | none |

`finalize` is a scheduler action, not a managed phase. Map it to an initial
`complete` handoff.

Launch a new assignment with:

    tmux_worker.py launch --repo <primary> --handoff <file>

After `inspect` reports a zero-exit checkpoint, revalidate live state and call:

    tmux_worker.py advance --repo <primary> --handoff <file> \
      --phase-snapshot <file> --expected-attempt-id <id> \
      --revalidated

The helper holds an exclusive transition lock, compares the active attempt,
validates the exit/result pair, derives the successor, writes the next attempt,
atomically changes `active.json`, and respawns the retained pane. A replayed
controller action fails closed.

Use `resume` only when an attempt was interrupted before a valid completed
checkpoint. It creates a new append-only attempt in the same phase and resumes
the exact recorded Codex thread. A phase transition always starts a fresh
thread. Recreating a lost tmux server requires full caller revalidation.

Accept terminal statuses `clean`, `blocked`, `canceled`, `claim_lost`, and
`failed`. Treat nonzero exit, missing/partial exit, malformed result, wrong
task/phase/attempt as failure. The controller never accepts a
worker-supplied next phase.

## Native Subagent Runtime

Use one persistent exact-task collaboration worker for the whole lifecycle and
the same immutable assignment. Do not mix runtimes within a run. Reviewer
subagents spawned inside a review use `fork_turns: "none"` and receive only the
minimal snapshot context; they are not ticket workers and do not expand the
ticket-worker cap.

## Normalized Graph And Review Gate

Build `swarm_wave.py` input from fresh provider reads. Each PR may contain
`state`, `branch`, `base_branch`, `head_sha`, compatibility `clean`,
`review_gate`, and `needs_reconcile`. `review_gate` is one of `not_ready`,
`zero_findings`, or `materially_clean`; when present it is authoritative.
`zero_findings` and `materially_clean` are stack-ready.

- No unmerged blocker: use the root base.
- Exactly one open stack-ready blocker PR: branch from its head and target its
  branch.
- More than one direct blocker: wait for every blocker PR to merge into the
  common target.
- Hold cycles and descendants of closed-unmerged, stale, incomplete, unknown,
  blocked, or claim-lost blockers.
- Multiple children of one stack-ready blocker may run concurrently.

Keep logical work-store blockers intact while developing a stacked child.

## Failure, Resume, And Evidence

- Provisioning failure: create no claim; clean only verified empty state.
- Claim loss: make no further code/provider change.
- Worker/push/PR failure: preserve branch, worktree, attempts, and exact missing
  operations; continue independent work.
- Swarm interruption: reconstruct from provider state, PR markers, branch
  metadata, registered worktrees, and attempt manifests.
- Worktree removal: require matching local and pushed PR head SHAs.
- Session cleanup: exact dead session only; preserve logs, branches, PRs, task
  records, and worktrees.

Count only live panes toward concurrency. Resume interrupted owned attempts
before new tasks. Keep every exited tmux session until explicit guarded cleanup.
Redirect verbose command output to attempt-local logs and expose only status,
duration, structured checkpoint data, and a failure tail capped at 200 lines or
16 KiB.
