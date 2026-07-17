---
name: brutal-worker
description: Own one exact BRUTAL.md implementation task or review finding through claim, isolated-worktree implementation, verification, stacked pull request creation, and an uncapped all-severity Brutal review/fix loop. Use for a task handed off by brutal-swarm or when the user supplies one stable task reference.
---

# Brutal Worker

Complete one exact work item and its pull request. Never select a replacement.

## Required Context

1. Require a stable task or review-finding reference. If none was supplied,
   request one or recommend `$brutal-swarm`; do not query for the next task.
2. Read `../brutal-shared/integration-resolver.md` and
   `../brutal-shared/support/contracts.md`.
3. Reuse a managed handoff's validated work-store identity, code-host identity,
   canonical local-store root, worktree, branch, base, and pull request. Resolve
   any missing identity and load both selected support modules before mutation.
   Treat runtime session names, state directories, and logs as observational;
   they grant no workflow authority.
4. Read `../brutal-swarm/references/parallel-execution.md`. For a standalone
   invocation, use `../brutal-swarm/scripts/worktree_manager.py` to create or
   resume the isolated worktree before editing.
5. Read `../brutal-inf-fix-loop/SKILL.md` and its required source skills.
6. Read repository rules from `AGENTS.md`, `CLAUDE.md`, `TARGET.md`, and their
   referenced workflow documents.

## Hard Rules

- Own only the handed-off work item, branch, worktree, and pull request.
- Select only `type:task` or `type:review-finding`; never implement a plan or
  investigation artifact.
- Never merge, approve, request changes, force-push, delete a remote branch, or
  create a second pull request for the same item.
- Preserve unrelated user changes. A managed worker edits only its isolated
  worktree; a standalone worker must create or safely resume one with the
  Brutal Swarm worktree helper.
- Keep the item `in_progress` until a fresh all-severity review is clean. Move
  it to `in_review` only then, and to `done` only after its pull request merged.

## Claim The Exact Item

1. Read the full body, history, comments, parent, blockers, assignment, and
   current pull-request link.
2. Handle existing state before code changes:
   - merged matching pull request: record acceptance and move the item to `done`
   - open matching pull request or branch: resume it
   - closed-unmerged pull request or identity mismatch: record `BLOCKED:` and stop
3. Claim from the expected state with the adapter's strongest assignment and
   transition operation. Add the run marker, then re-read state and ownership.
   Continue only when the claim is proven; otherwise return `claim_lost` without
   changing code, branch, or pull request.
4. A blocked dependency may remain logically open only when the task has one
   direct blocker, its pull request is open and clean, and the handoff uses that
   blocker branch as this task's base. A task with several direct blockers waits
   until every blocker pull request merges into their common target.

## Implement And Publish

1. Confirm that the current worktree, branch, base branch, base SHA, and task
   marker match the handoff.
2. Identify affected files, existing patterns, tests, and verification commands.
3. Implement with TDD when practical: make the focused test fail, implement the
   smallest correct change, and make it pass.
4. Remove unnecessary code and accidental churn. Run required formatting,
   focused tests, and repository checks.
5. Self-review correctness, reliability, error handling, security, performance,
   resource usage, simplicity, and maintainability. Fix every material issue.
6. Commit atomic verified changes and push normally.
7. Find a pull request by exact marker and head branch before creating one. Use:

       <!-- brutal-worker:v1:<stable-task-ref> -->
       Source: brutal-worker
       Work item: <stable ref or URL>
       Parent: <stable ref or none>
       Blocked by: <stable refs or none>
       Stack base: <branch and blocker ref or root>
       Verification: <commands and results>

   Title it `[<task-ref>] <task title>` and open it ready for review against the
   handed-off base. Patch only the matching owned pull request on retry.

## Review Until Clean

Run `$brutal-inf-fix-loop` against this exact open pull request in the same
worktree. Reuse the managed integrations and canonical local work-store root.
Do not impose a pass, time, token, cost, commit, or no-progress limit. Relay
each pass result to the swarm when one exists.

After a fresh review returns `validated_finding_count: 0`:

1. Re-run required verification for the final head.
2. Update the task with changed files, commands/results, commits, branch, pull
   request, stack base, clean review id, and residual risks.
3. Move the task to `in_review` and return a structured result containing task,
   branch, base, pull request, local and remote head, verification, review id,
   and `cleanup_eligible: true`.

On a hard source-skill guard or user interruption, add an exact `BLOCKED:` or
`CANCELED:` record, leave the task in `in_progress`, preserve the worktree, and
return the remaining review occurrences and recovery state. Never call that
result clean.

When running under tmux, always return the structured result expected by the
supervisor. Do not kill, rename, or clean up the containing session.
