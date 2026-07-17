---
name: brutal-swarm
description: Coordinate multiple BRUTAL.md implementation tasks through parallel tmux Codex workers or native subagents, with one isolated git worktree and stacked pull request per task. Use when Codex should drain a task graph concurrently while preserving exact ticket ownership and blocker-based PR chains.
---

# Brutal Swarm

Schedule task workers without taking ownership of their tickets or pull requests.

## Required Context

1. Read `../brutal-shared/integration-resolver.md` and
   `../brutal-shared/support/contracts.md`.
2. Resolve one work store and one code host, load both support modules, and
   retain their normalized identities for every worker.
3. Read `../brutal-worker/SKILL.md` and
   `references/parallel-execution.md` completely.
4. Read repository rules from `AGENTS.md`, `CLAUDE.md`, `TARGET.md`, and their
   referenced workflow documents.

## Start A Run

1. Discover resumable `in_progress` and `in_review` work plus unblocked or
   stack-ready `todo` artifacts of type `task` or `review_finding`.
2. Group candidates by plan parent. Use an explicitly requested parent; infer
   the only candidate graph; otherwise ask the user to select one graph.
3. Resolve an explicit target branch or the code host's default branch. Record
   its remote head. Never include uncommitted changes from the initiating
   worktree.
4. Ask the user for the maximum number of ticket workers to run concurrently.
   This blocking question is mandatory on every run. Treat the answer as a
   concurrency cap, disclose any lower platform capacity, and use the smaller
   value.
5. For a local work store, resolve its canonical absolute root against the
   primary git worktree before launching linked worktrees.
6. Use `scripts/runtime_config.py` to resolve `execution.worker_runtime`,
   defaulting to `tmux`. Accept only `tmux` or `subagent`. Validate the selected
   runtime before creating a worktree or claiming a task; never fall back
   implicitly.

## Drain The Graph

Use `scripts/swarm_wave.py` with the normalized graph described in the reference
to choose each deterministic wave.

For every selected artifact:

1. Use `scripts/worktree_manager.py` to create or safely resume its branch and
   sibling worktree. Provision worktrees serially before launching workers.
2. Launch one persistent worker in that worktree with the exact managed handoff
   from the reference. For `tmux`, use `scripts/tmux_worker.py`; for `subagent`,
   use a native collaboration worker. Instruct it to use `$brutal-worker` and no
   other task.
3. After handoff, do not claim, comment on, transition, implement, push, review,
   or edit that task or pull request. The swarm may read state and relay worker
   progress.
4. If the worker loses its claim, remove only the verified empty worktree and
   schedule the next candidate. If it blocks after making progress, preserve
   its worktree and exclude its descendants while independent workers continue.
5. After a clean worker result, remove the worktree only when the returned local
   head equals the verified pushed pull-request head. Keep its local and remote
   branches while the pull request is open.

Rebuild the graph whenever a worker reaches a terminal result. Continue waves
until no resumable, reconcilable, or stack-ready artifact remains. Do not stop
after the first wave or after launching the requested number in total.

For tmux runs, count only live worker panes toward the cap. Keep every exited
session, including successful sessions, until explicit guarded cleanup. Runtime
logs and sessions are not workflow truth and never authorize task transitions.

## Reconcile Existing Stacks

Prioritize exact-task worker handoffs that:

- move a ticket whose pull request merged from `in_review` to `done`
- update an open child after its base branch advanced or its blocker merged
- resume an `in_progress` task with a matching branch or pull request

Make each child worker merge the new base normally, push, retarget its own pull
request when needed, rerun verification, and complete a fresh infinite fix
loop. Never merge a pull request or force-push a branch.

## Final Response

Report integrations, selected graph, requested and effective concurrency,
selected runtime, workers launched, task/session/worktree/branch/pull-request
mappings, clean and blocked results, retained sessions and worktrees, attach and
cleanup commands, and the reasons remaining artifacts are not stack-ready.
