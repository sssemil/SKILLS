---
name: brutal-worker
description: Own one exact BRUTAL.md task or review finding through claim, isolated implementation, verification, stacked pull request publication, and an uncapped material-correctness review/fix loop. Managed tmux workers execute one phase per fresh Codex thread.
---

# Brutal Worker

Complete one exact work item and its pull request. Never select a replacement.

## Required Context

Always require the stable task reference and read applicable repository rules.
Read `../brutal-shared/integration-resolver.md` and
`../brutal-shared/support/contracts.md`. Reuse a managed assignment’s validated
work-store/code-host identities, canonical local root, worktree, branch, and
base; resolve only missing data needed by the current phase.

For standalone work, also read
`../brutal-swarm/references/parallel-execution.md`, create or resume the isolated
worktree with `../brutal-swarm/scripts/worktree_manager.py`, and read
`../brutal-inf-fix-loop/SKILL.md` plus its source skills.

For managed tmux work, the immutable handoff establishes assignment identity;
the phase snapshot supplies revalidated mutable state. Runtime names, logs, and
old snapshots are observational and grant no provider authority.
Validate the context-file checksum and every `{path, sha256}` reference before
using it. Echo `context_sha256` in the managed result.

## Hard Rules

- Own only the handed-off item, branch, worktree, and pull request.
- Select only `task` or `review_finding`; never implement a plan or
  investigation.
- Never merge, approve, request changes, force-push, delete a remote branch, or
  create a second pull request for the item.
- Preserve unrelated changes and edit only the isolated worktree.
- Keep the item `in_progress` until a fresh review has no CRITICAL or MAJOR.
  Then it may move to `in_review`; move it to `done` only after its PR merged.

## Managed Phase Protocol

When the prompt contains a managed phase snapshot, do only that phase and
return the supervisor’s exact result. Do not continue into the next phase.

If the ticket has `## Writable Directory` and BRUTAL.md configures
`execution.edit_sandbox_command`, use `scoped_edit.py` to launch an editing
child in that directory. The child may edit only: it must not commit, push, or
call providers. After it exits, reject changed paths outside the boundary;
then the task worker reviews, verifies, commits, pushes, and owns the PR as
normal. Missing commands, path escapes, or outside changes return `blocked`
with the worktree preserved. This is a repository write boundary, not a
confidentiality or network sandbox.

### `work`

Read the full item, history, parent/blockers, assignment, and existing PR link.
Prove the exact claim from the expected state before changing code. Validate
worktree, branch, base branch/SHA, and branch task marker. Implement, test,
self-review, commit, push, and find-or-create the single marked PR. Return a
checkpoint with current base/head, PR, verification, and zeroed review fields.

### `review`

Read `../brutal-inf-fix-loop/SKILL.md` and
`../brutal-pr-review/SKILL.md`. Use only the exact PR/base/head snapshot and
relevant repository rules. Run one fresh `material_convergence` pass. Return
counts for all severities, review id, queued/unhandled counts, summary status,
and residual MINOR/NIT findings. Exit after the checkpoint.

### `fix`

Read `../brutal-inf-fix-loop/SKILL.md` and
`../brutal-pr-finding-fixer/SKILL.md`. Drain the full generated all-severity
queue for the supplied review occurrence, verify, push, re-read base/head, and
return a checkpoint. Do not start a review.

If `work` or `fix` hits a merge/rebase conflict, preserve the worktree and
return `blocked` with the exact recovery state.

### `handoff`

This phase is reached only after a fresh review has zero CRITICAL and zero
MAJOR. Revalidate PR identity, base/head, task ownership, queue state, and
required checks. Reuse same-head verification only when the complete base/head
snapshot still matches and checks still pass; otherwise rerun it. Record
changed files, commands/results, commits, PR/base, review id, completion kind,
and residual MINOR/NIT findings on the task. Move it to `in_review` and return
terminal `clean` with `zero_findings` or `materially_clean`.

### `complete`

After a matching PR is verified merged, record acceptance, move the item to
`done`, and return terminal `clean` with `completion_kind: merged`. This is the
only preassigned phase that replaces the scheduler’s post-merge `finalize`
action; never use `finalize` as a managed worker phase.

The supervisor alone derives legal phase transitions. A fresh phase uses a new
Codex thread. Resume the exact recorded thread only when the current attempt was
interrupted in the same phase. Return `blocked`, `canceled`, `claim_lost`, or
`failed` with exact recovery state on hard stops.

## Standalone Lifecycle

1. Read and claim the exact item. Resume a matching open PR/branch; complete a
   matching merged PR; block on closed-unmerged or identity mismatch.
2. Confirm the isolated branch/base and implement the smallest verified change.
3. Commit and push normally. Find the PR by exact marker and head before
   creating one against the handed-off base:

       <!-- brutal-worker:v1:<stable-task-ref> -->
       Source: brutal-worker
       Work item: <stable ref or URL>
       Parent: <stable ref or none>
       Blocked by: <stable refs or none>
       Stack base: <branch and blocker ref or root>
       Verification: <commands and results>

4. Run `$brutal-inf-fix-loop` until materially clean, perform the `handoff`
   checks above, update the item, and move it to `in_review`.

Redirect verbose builds, tests, diffs, and provider output to run-local
temporary logs. Report command status and duration. On failure, include only
the last 200 lines or 16 KiB, whichever is smaller.
