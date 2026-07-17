# Parallel Execution Contract

Read this reference before scheduling a Brutal Swarm run.

## Managed Worker Handoff

Pass one exact handoff to each worker:

```yaml
mode: managed
run_id: <safe unique token>
task_ref: <stable provider ref>
task_kind: task | review_finding
worker_runtime: tmux | subagent
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
stacked_on:
  task_ref: <single blocker ref or null>
  pr: <provider PR ref or null>
```

The handoff is immutable. The tmux supervisor resolves and writes its two
`runtime` fields before starting Codex; native subagent handoffs use `null`.
Runtime fields are observational and grant no task, branch, pull-request, or
provider authority. If live provider state contradicts the handoff, stop and
report the stale field rather than silently choosing another task or base.

## Worker Runtimes

Resolve `execution.worker_runtime` through the shared resolver before creating
worktrees. Missing configuration means `tmux`.

For `tmux`, use `../scripts/tmux_worker.py`. It launches one non-ephemeral
`codex exec` process in the exact task worktree, sends the handoff through a
private prompt file, and retains its tmux session after exit. Treat task, pull
request, Git, and worktree state as truth; JSONL logs and tmux metadata are
observability and recovery hints only. A lost tmux server never authorizes a
task transition or replacement worker.

Call `launch --repo <primary> --handoff <file>` for a new assignment and retain
its JSON response. Use `inspect` to distinguish live workers from retained dead
panes, `resume` for the exact recorded Codex thread, and `cleanup` only on an
explicit session-cleanup request. Mutating commands require the same exact repo,
task, branch, worktree, repository identity, and tmux socket. The helper returns
safe attach and capture argv; the pane mirrors live Codex JSONL while the same
events remain in the protected state directory.

On a later swarm run, `inspect` may rediscover a retained task using the primary
repo, exact task ref, repository identity, and original tmux socket without an
existing worktree. Recreate the manifest's recorded worktree path with
`worktree_manager.py create --path` before resuming; do not move the persistent
task session to a newly derived run path.

Accept worker statuses `clean`, `blocked`, `canceled`, `claim_lost`, and
`failed`. Treat a nonzero process exit, malformed result, or mismatched task ref
as `failed` even if a partial result claims success.

For `subagent`, launch the existing persistent native collaboration worker with
the same exact handoff. Do not mix runtimes within one run. Never fall back from
one runtime to the other implicitly.

Count only live workers toward the concurrency cap. A retained exited tmux
session occupies no slot.

## Normalized Graph

Build the JSON consumed by `../scripts/swarm_wave.py` from fresh provider reads.
Use stable refs and deterministic provider ordering. Each task includes:

- `ref`, `kind`, `state`, `order_key`, and optional numeric `priority`
- `blockers` as stable refs
- `claimable`, `decision_complete`, and `owned` booleans
- optional `branch`, `base_branch`, and `base_sha`
- optional `pr` with `state`, `branch`, `base_branch`, `head_sha`, `clean`, and
  `needs_reconcile`

Pass `root_base.branch`, `root_base.sha`, and the effective worker `limit`. Treat
the helper output as scheduling advice; re-read live state before every claim.

## Stack-Ready Rules

- No unmerged blocker: use the root base.
- Exactly one open, clean blocker pull request: branch from its head and target
  its head branch.
- More than one direct blocker: wait until every blocker pull request merges
  into the root base, even when only one remains unmerged. Verify the merge
  targets before normalizing them as satisfied.
- Dependency cycle: hold every participating task and report the cycle; never
  linearize it implicitly.
- Closed-unmerged, blocked, stale, incomplete, unknown, or claim-lost blocker:
  hold every descendant.
- Multiple children of one clean blocker may run concurrently.

Logical work-store blockers remain intact while a child is developed on a
single blocker branch. Never delete or falsify dependency relationships to make
an adapter report the child as unblocked.

## Pull-Request Reconciliation

GitHub automatically retargets an open child only when its merged base branch is
deleted. On every later run, verify the actual base instead of assuming that
happened.

For each affected child, hand the child task to its own worker. That worker:

1. fetches the new base and records its head
2. merges it normally into the child branch without rewriting history
3. resolves conflicts and reruns required verification
4. pushes normally, then changes the PR base when needed
5. runs a fresh infinite review/fix loop

A parent worker never edits a child's branch, task, or pull request.

## Failure And Resume

- Provisioning failure: create no task claim; clean only verified empty state.
- Claim loss: make no code or provider change after the failed claim.
- Worker failure: preserve task branch and worktree; continue independent work.
- Push or PR failure: keep `in_progress`, record the exact completed and missing
  operations, and resume the same identity later.
- Swarm interruption: reconstruct from work-store state, PR markers, branch
  metadata, and registered worktrees; do not require a local run manifest.
- Tmux interruption: inspect the exact retained session and state directory.
  Resume a dead matching Codex session when its ID is recorded. If it is absent,
  launch a fresh exact-task process only after revalidating live task, PR,
  branch, and worktree identity. Never resume a live pane.

Remove a successful worktree only after the worker returns matching local and
provider head SHAs. Pass the exact task ref to cleanup and require matching
stored branch metadata. Keep task branches until their PRs are merged or closed
by a human workflow.

When resuming a branch found through its PR marker, pass that exact branch with
`worktree_manager.py create --branch`; do not derive a replacement from a title
that may have changed.

Keep every tmux session after exit. Report its attach, capture, and exact cleanup
commands. Explicit session cleanup must validate repository and task metadata,
preserve runtime logs, and never remove branches, pull requests, work-store
records, or worktrees.
