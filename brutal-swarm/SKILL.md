---
name: brutal-swarm
description: Drain a BRUTAL.md task graph through parallel isolated workers and stacked pull requests. Managed workers use append-only phases with fresh execution context.
---

# Brutal Swarm

Schedule exact-task workers without taking ownership of their tickets or pull
requests.

## Required Context

1. Read `../brutal-shared/integration-resolver.md`,
   `../brutal-shared/support/contracts.md`, `../brutal-worker/SKILL.md`, and
   `references/parallel-execution.md` completely.
2. Resolve one work store and code host, load both support modules, and retain
   their normalized identities.
3. Read applicable repository workflow rules.

## Start A Run

1. Discover resumable `in_progress`/`in_review` work and stack-ready `todo`
   artifacts of kind `task` or `review_finding`. Select one plan graph.
2. Resolve the explicit or default root branch and record its remote head.
   Never inherit uncommitted changes from the initiating worktree.
3. Ask for the maximum concurrent ticket workers on every run. Use the smaller
   of that answer and platform capacity.
4. Resolve `execution.worker_runtime` with `scripts/runtime_config.py` before
   claiming or provisioning. Missing means `tmux`; accept only `tmux` or
   `subagent` and never fall back implicitly.
5. For a local work store, resolve its canonical absolute root against the
   primary worktree.

## Drain The Graph

Use `scripts/swarm_wave.py` on fresh normalized provider reads for every wave.
Resume owned attempts before starting `todo` work.

For each selected artifact:

1. Provision or safely resume its sibling worktree serially with
   `scripts/worktree_manager.py`.
2. Pass the exact managed handoff from the execution reference. Use
   `scripts/tmux_worker.py` for tmux, or one persistent native collaboration
   worker for the subagent runtime. Instruct it to use `$brutal-worker` for only
   that task.
3. After handoff, do not claim, comment, transition, implement, push, review, or
   edit that task/PR. The swarm may re-read state, advance managed phases, and
   relay progress.
4. Preserve progress on failure. Remove only a verified empty worktree after
   claim loss. Exclude blocked descendants while independent work continues.

For tmux, count only live panes toward the concurrency cap. Retained dead panes
occupy no slot. When a pane returns a valid zero-exit checkpoint, revalidate the
task, ownership, PR, branch/base/head, and checks; write a mutable phase
snapshot; then call `tmux_worker.py advance` with the active attempt id and
revalidated snapshot. The controller derives the next phase. Never resume a
completed checkpoint or reuse its Codex thread across phases.

Managed prompts contain only the phase, context-file path, and result path.
Bulk ticket, diff, check, and finding data stays in one run-local context file.

Prioritize an interrupted same-phase resume before new work, still within the
cap. Use exact-thread `resume` only for that interruption. Every phase and retry
gets an append-only attempt directory; never overwrite or accept a stale
attempt, missing exit record, or partial result.

After terminal `clean`, remove the worktree only when the returned local head
equals the verified pushed PR head. Keep branches while PRs remain open. A
`zero_findings` or `materially_clean` review gate is stack-ready; literal
`pr.clean` remains a compatibility input, not the only readiness signal.

Rebuild the graph whenever a worker reaches a checkpoint or terminal result.
Continue until no resumable, reconcilable, or stack-ready artifact remains.
Do not stop after the first wave.

## Reconcile Existing Stacks

Prioritize exact-task handoffs that complete merged tickets, update children
after a base advances, or resume matching owned work. A child worker merges the
new base normally, resolves conflicts, verifies, pushes, retargets when needed,
and re-enters the material-correctness review/fix loop. Never merge a PR,
force-push, or let a parent worker edit a child.

## Operational Output

Keep full tmux JSONL, test, diff, and provider output in protected run/attempt
logs. Relay only status, duration, checkpoint summary, and on failure the last
200 lines or 16 KiB, whichever is smaller. Logs and sessions are observability,
not workflow truth.

## Final Response

Report integrations, graph, requested/effective concurrency, runtime, worker
and phase attempts, task/session/worktree/branch/PR mappings, completion kinds,
residual lower-severity findings, blocked results, retained evidence, safe
attach/cleanup commands, and reasons remaining artifacts are not stack-ready.
